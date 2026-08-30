from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.property import Property, PriceHistory
from backend.importers.base_importer import make_content_hash
from backend.ai.analyzer import analyze_property, apply_analysis
from backend.sources.base import FetchResult

def ingest_items(db: Session, items: List[Dict[str, Any]], run_analysis: bool = True) -> Dict[str, int]:
    inserted = updated = skipped = price_changed = 0
    for item in items:
        source = item.get("source") or "import"
        lid = str(item.get("source_listing_id") or make_content_hash(item))
        item["source"] = source
        item["source_listing_id"] = lid
        item["content_hash"] = item.get("content_hash") or make_content_hash(item)
        if not item.get("url"):
            item["url"] = f"{source}://{lid}"
        existing = db.query(Property).filter(Property.source == source, Property.source_listing_id == lid).first()
        if existing:
            new_price = item.get("price")
            if new_price and existing.price and float(new_price) != float(existing.price):
                db.add(PriceHistory(property_id=existing.id, price=float(existing.price), source=source))
                price_changed += 1
            if existing.content_hash == item["content_hash"]:
                existing.last_seen = datetime.utcnow()
                skipped += 1
                continue
            for k, v in item.items():
                if k in ("id",) or v is None: continue
                if hasattr(existing, k): setattr(existing, k, v)
            existing.last_seen = datetime.utcnow()
            if run_analysis: apply_analysis(existing, analyze_property(existing))
            updated += 1
        else:
            fields = {k: v for k, v in item.items() if hasattr(Property, k)}
            prop = Property(**fields)
            prop.first_seen = datetime.utcnow()
            prop.last_seen = datetime.utcnow()
            if run_analysis: apply_analysis(prop, analyze_property(prop))
            db.add(prop)
            inserted += 1
    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "price_changed": price_changed}

def run_source(db: Session, source_name: str, limit: int = 10, **kwargs) -> FetchResult:
    from backend.sources.registry import get_source, record_run, init_registry
    init_registry()
    src = get_source(source_name)
    if not src:
        return FetchResult(source=source_name, status="ERROR", message="Unknown source")
    result = src.fetch(limit=limit, **kwargs)
    if result.items:
        stats = ingest_items(db, result.items, run_analysis=True)
        result.inserted = stats["inserted"]
        result.updated = stats["updated"]
        result.skipped = stats["skipped"]
        result.message += f" | DB: +{stats['inserted']} ~{stats['updated']} skip={stats['skipped']} price_chg={stats['price_changed']}"
    record_run(source_name, result)
    return result

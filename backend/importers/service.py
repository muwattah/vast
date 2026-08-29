"""
Import service: upsert properties, avoid duplicates, optionally re-analyze.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from backend.models.property import Property
from backend.importers.base_importer import make_content_hash
from backend.ai.analyzer import analyze_property, apply_analysis

logger = logging.getLogger(__name__)


def upsert_properties(db: Session, items: List[Dict[str, Any]], run_analysis: bool = True) -> Dict[str, int]:
    created = updated = skipped = analyzed = 0

    for item in items:
        source = item.get("source") or "import"
        listing_id = item.get("source_listing_id") or make_content_hash(item)
        item["source"] = source
        item["source_listing_id"] = listing_id
        item["content_hash"] = item.get("content_hash") or make_content_hash(item)

        existing = (
            db.query(Property)
            .filter(Property.source == source, Property.source_listing_id == listing_id)
            .first()
        )

        if existing:
            if existing.content_hash == item["content_hash"]:
                existing.last_seen = datetime.utcnow()
                skipped += 1
                continue
            for k, v in item.items():
                if k in ("id",) or v is None:
                    continue
                if hasattr(existing, k):
                    setattr(existing, k, v)
            existing.last_seen = datetime.utcnow()
            if run_analysis:
                analysis = analyze_property(existing)
                apply_analysis(existing, analysis)
                analyzed += 1
            updated += 1
        else:
            prop = Property(**{k: v for k, v in item.items() if hasattr(Property, k)})
            prop.first_seen = datetime.utcnow()
            prop.last_seen = datetime.utcnow()
            if run_analysis:
                analysis = analyze_property(prop)
                apply_analysis(prop, analysis)
                analyzed += 1
            db.add(prop)
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "analyzed": analyzed}

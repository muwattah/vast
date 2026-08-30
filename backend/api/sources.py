from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database.db import get_db
from backend.models.property import Property
from backend.sources.registry import init_registry, list_sources
from backend.sources.pipeline import run_source, ingest_items
from backend.sources.url_import import fetch_url_listing

router = APIRouter()

@router.get("/sources")
def get_sources():
    init_registry()
    return {"sources": list_sources()}

@router.post("/sources/{source_name}/run")
def run_named_source(source_name: str, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    result = run_source(db, source_name, limit=limit)
    return {"source": result.source, "status": result.status, "discovered": result.discovered,
            "parsed": result.parsed, "rejected": result.rejected, "inserted": result.inserted,
            "updated": result.updated, "skipped": result.skipped, "duration_ms": result.duration_ms,
            "message": result.message, "errors": result.errors[:10]}

class UrlImportIn(BaseModel):
    url: str

@router.post("/import/url")
def import_from_url(body: UrlImportIn, db: Session = Depends(get_db)):
    try:
        item = fetch_url_listing(body.url)
    except Exception as e:
        raise HTTPException(400, f"Fetch failed: {e}")
    stats = ingest_items(db, [item], run_analysis=True)
    return {"status": "ok", "item": {"title": item.get("title"), "price": item.get("price"),
            "postal_code": item.get("postal_code"), "source": item.get("source"), "url": item.get("url")}, "db": stats}

@router.get("/data-mode/stats")
def data_mode_stats(db: Session = Depends(get_db)):
    total = db.query(Property).filter(Property.is_active == True).count()
    demo = db.query(Property).filter(Property.is_active == True, Property.source == "demo").count()
    by_source = {}
    for src in ("demo", "import", "manual", "biddit", "immoweb", "zimmo", "url_import"):
        c = db.query(Property).filter(Property.source == src, Property.is_active == True).count()
        if c: by_source[src] = c
    return {"total": total, "demo_listings": demo, "real_listings": total - demo, "by_source": by_source}

"""
Scrape / refresh endpoints.
Real scrapers are disabled by default (legal + technical constraints).
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.config import get_settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.enable_scrapers:
        return {
            "status": "disabled",
            "message": "Live scrapers are disabled by default. Set ENABLE_SCRAPERS=true and implement legal data sources. Demo data is currently used.",
            "sources": {
                "immoweb": "disabled (ToS / anti-bot)",
                "zimmo": "disabled",
                "immovlan": "disabled",
                "biddit": "disabled",
                "demo": "active"
            }
        }
    return {"status": "queued", "message": "Scrape job would start here"}


@router.get("/scrape/status")
def scrape_status():
    return {
        "last_run": None,
        "status": "idle",
        "note": "Live scraping not enabled. Use demo data or configure allowed sources."
    }

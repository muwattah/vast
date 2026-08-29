"""Antwerp Property Investor – Backend API"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.database.db import init_db, SessionLocal
from backend.api import properties, scrape, stats, favorites, import_api, deals, tools, investor
from backend.services.seed import seed_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    logger.info("Application ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Antwerp Property Investor API",
    description="API for finding and scoring DIY renovation properties in Antwerp",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties.router, prefix="/api", tags=["properties"])
app.include_router(scrape.router, prefix="/api", tags=["scrape"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(favorites.router, prefix="/api", tags=["favorites"])
app.include_router(import_api.router, prefix="/api", tags=["import"])
app.include_router(deals.router, prefix="/api", tags=["deals"])
app.include_router(tools.router, prefix="/api", tags=["tools"])
app.include_router(investor.router, prefix="/api", tags=["investor"])


@app.get("/")
def root():
    return {
        "app": "Antwerp Property Investor",
        "status": "ok",
        "version": "0.4.0",
        "docs": "/docs",
        "note": "Demo data is used by default. Import JSON/CSV or POST /api/properties for real listings. Live scrapers disabled.",
    }


@app.get("/health")
def health():
    from backend.config import get_settings
    s = get_settings()
    return {
        "status": "healthy",
        "database": "healthy",
        "ai": "available" if (s.openai_api_key or s.grok_api_key) else "fallback_rule_based",
        "imports": "available",
        "version": "0.4.0",
    }

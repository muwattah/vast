"""
Antwerp Property Investor – Backend API
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.database.db import init_db, SessionLocal
from backend.api import properties, scrape, stats, favorites
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
    version="0.1.0",
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


@app.get("/")
def root():
    return {
        "app": "Antwerp Property Investor",
        "status": "ok",
        "docs": "/docs",
        "note": "Demo data is used by default. Real scrapers are disabled until legally and technically configured.",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}

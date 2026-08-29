"""Import endpoints: JSON, CSV, and manual property create."""
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from backend.database.db import get_db
from backend.models.property import Property
from backend.importers.json_importer import JsonImporter
from backend.importers.csv_importer import CsvImporter
from backend.importers.service import upsert_properties
from backend.importers.base_importer import make_content_hash, detect_renovation_flags
from backend.ai.analyzer import analyze_property, apply_analysis

router = APIRouter()


class ManualPropertyIn(BaseModel):
    title: str
    price: Optional[float] = None
    postal_code: Optional[str] = None
    city: Optional[str] = "Antwerpen"
    district: Optional[str] = None
    address: Optional[str] = None
    property_type: Optional[str] = "huis"
    living_area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    year_built: Optional[int] = None
    epc_label: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source_listing_id: Optional[str] = None
    is_to_renovate: bool = False
    is_fully_to_renovate: bool = False
    is_investment: bool = False


@router.post("/import/json")
async def import_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith((".json", ".txt")):
        raise HTTPException(400, "Expected a .json file")
    content = await file.read()
    try:
        items = JsonImporter().parse(content, file.filename)
    except Exception as e:
        raise HTTPException(400, f"JSON parse error: {e}")
    if not items:
        raise HTTPException(400, "No properties found in file")
    stats = upsert_properties(db, items, run_analysis=True)
    return {"status": "ok", "imported": stats, "count": len(items)}


@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(400, "Expected a .csv file")
    content = await file.read()
    try:
        items = CsvImporter().parse(content, file.filename)
    except Exception as e:
        raise HTTPException(400, f"CSV parse error: {e}")
    if not items:
        raise HTTPException(400, "No properties found in file")
    stats = upsert_properties(db, items, run_analysis=True)
    return {"status": "ok", "imported": stats, "count": len(items)}


@router.post("/properties")
def create_property(body: ManualPropertyIn, db: Session = Depends(get_db)):
    flags = detect_renovation_flags(f"{body.title} {body.description or ''}")
    data = {
        "source": "manual",
        "source_listing_id": body.source_listing_id or make_content_hash(body.model_dump()),
        "url": body.url or f"manual://{body.title[:40]}",
        "title": body.title,
        "price": body.price,
        "address": body.address,
        "postal_code": body.postal_code,
        "city": body.city,
        "district": body.district,
        "property_type": body.property_type,
        "living_area": body.living_area,
        "bedrooms": body.bedrooms,
        "bathrooms": body.bathrooms,
        "year_built": body.year_built,
        "epc_label": body.epc_label,
        "description": body.description,
        "images": [],
        "features": [],
        "is_to_renovate": body.is_to_renovate or flags["is_to_renovate"],
        "is_fully_to_renovate": body.is_fully_to_renovate or flags["is_fully_to_renovate"],
        "is_investment": body.is_investment or flags["is_investment"],
        "is_active": True,
        "first_seen": datetime.utcnow(),
        "last_seen": datetime.utcnow(),
    }
    data["content_hash"] = make_content_hash(data)
    existing = db.query(Property).filter(
        Property.source == "manual", Property.source_listing_id == data["source_listing_id"]
    ).first()
    if existing:
        raise HTTPException(409, "Property with this listing id already exists")
    prop = Property(**{k: v for k, v in data.items() if hasattr(Property, k)})
    analysis = analyze_property(prop)
    apply_analysis(prop, analysis)
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return {"status": "created", "id": prop.id, "investment_score": prop.investment_score}

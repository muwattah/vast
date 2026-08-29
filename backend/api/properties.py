"""
Property listing and detail endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from pydantic import BaseModel
from datetime import datetime

from backend.database.db import get_db
from backend.models.property import Property

router = APIRouter()


class PropertyOut(BaseModel):
    id: int
    source: str
    title: str
    price: Optional[float]
    postal_code: Optional[str]
    city: Optional[str]
    district: Optional[str]
    property_type: Optional[str]
    living_area: Optional[float]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    epc_label: Optional[str]
    epc_score: Optional[float]
    is_to_renovate: bool
    is_fully_to_renovate: bool
    is_investment: bool
    investment_score: Optional[float]
    diy_score: Optional[float]
    margin_score: Optional[float]
    estimated_profit_min: Optional[float]
    estimated_profit_max: Optional[float]
    estimated_roi_min: Optional[float]
    estimated_roi_max: Optional[float]
    estimated_renovation_cost_min: Optional[float]
    estimated_renovation_cost_max: Optional[float]
    estimated_after_renovation_value_min: Optional[float]
    estimated_after_renovation_value_max: Optional[float]
    renovation_level: Optional[str]
    ai_summary: Optional[str]
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    url: str
    price_per_m2: Optional[float] = None

    class Config:
        from_attributes = True


class PropertyDetail(PropertyOut):
    address: Optional[str]
    description: Optional[str]
    images: Optional[list]
    features: Optional[list]
    year_built: Optional[int]
    ai_opportunities: Optional[list]
    ai_risks: Optional[list]
    diy_tasks: Optional[list]
    professional_tasks: Optional[list]
    price_score: Optional[float]
    renovation_score: Optional[float]
    location_score: Optional[float]
    risk_score: Optional[float]


@router.get("/properties", response_model=List[PropertyOut])
def list_properties(
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_area: Optional[float] = Query(None),
    max_area: Optional[float] = Query(None),
    epc: Optional[List[str]] = Query(None),
    min_score: Optional[float] = Query(None),
    only_diy: bool = Query(False),
    only_renovate: bool = Query(False),
    property_type: Optional[str] = Query(None),
    postal_code: Optional[str] = Query(None),
    sort: str = Query("best"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(Property).filter(Property.is_active == True)

    if min_price is not None:
        q = q.filter(Property.price >= min_price)
    if max_price is not None:
        q = q.filter(Property.price <= max_price)
    if min_area is not None:
        q = q.filter(Property.living_area >= min_area)
    if max_area is not None:
        q = q.filter(Property.living_area <= max_area)
    if epc:
        q = q.filter(Property.epc_label.in_([e.upper() for e in epc]))
    if min_score is not None:
        q = q.filter(Property.investment_score >= min_score)
    if only_diy:
        q = q.filter(Property.diy_score >= 7.0)
    if only_renovate:
        q = q.filter((Property.is_to_renovate == True) | (Property.is_fully_to_renovate == True))
    if property_type:
        q = q.filter(Property.property_type == property_type)
    if postal_code:
        q = q.filter(Property.postal_code == postal_code)

    if sort == "best":
        q = q.order_by(desc(Property.investment_score).nullslast())
    elif sort == "diy":
        q = q.order_by(desc(Property.diy_score).nullslast())
    elif sort == "margin":
        q = q.order_by(desc(Property.estimated_profit_max).nullslast())
    elif sort == "price":
        q = q.order_by(asc(Property.price).nullslast())
    elif sort == "price_m2":
        q = q.order_by(asc(Property.price / Property.living_area).nullslast())
    elif sort == "area":
        q = q.order_by(desc(Property.living_area).nullslast())
    elif sort == "newest":
        q = q.order_by(desc(Property.first_seen))
    else:
        q = q.order_by(desc(Property.investment_score).nullslast())

    results = q.offset(offset).limit(limit).all()
    out = []
    for p in results:
        data = {
            "id": p.id,
            "source": p.source,
            "title": p.title,
            "price": p.price,
            "postal_code": p.postal_code,
            "city": p.city,
            "district": p.district,
            "property_type": p.property_type,
            "living_area": p.living_area,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "epc_label": p.epc_label,
            "epc_score": p.epc_score,
            "is_to_renovate": bool(p.is_to_renovate),
            "is_fully_to_renovate": bool(p.is_fully_to_renovate),
            "is_investment": bool(p.is_investment),
            "investment_score": p.investment_score,
            "diy_score": p.diy_score,
            "margin_score": p.margin_score,
            "estimated_profit_min": p.estimated_profit_min,
            "estimated_profit_max": p.estimated_profit_max,
            "estimated_roi_min": p.estimated_roi_min,
            "estimated_roi_max": p.estimated_roi_max,
            "estimated_renovation_cost_min": p.estimated_renovation_cost_min,
            "estimated_renovation_cost_max": p.estimated_renovation_cost_max,
            "estimated_after_renovation_value_min": p.estimated_after_renovation_value_min,
            "estimated_after_renovation_value_max": p.estimated_after_renovation_value_max,
            "renovation_level": p.renovation_level,
            "ai_summary": p.ai_summary,
            "first_seen": p.first_seen,
            "last_seen": p.last_seen,
            "url": p.url,
            "price_per_m2": p.price_per_m2(),
        }
        out.append(PropertyOut(**data))
    return out


@router.get("/properties/{property_id}", response_model=PropertyDetail)
def get_property(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    data = {
        "id": p.id, "source": p.source, "title": p.title, "price": p.price,
        "postal_code": p.postal_code, "city": p.city, "district": p.district,
        "property_type": p.property_type, "living_area": p.living_area,
        "bedrooms": p.bedrooms, "bathrooms": p.bathrooms,
        "epc_label": p.epc_label, "epc_score": p.epc_score,
        "is_to_renovate": bool(p.is_to_renovate),
        "is_fully_to_renovate": bool(p.is_fully_to_renovate),
        "is_investment": bool(p.is_investment),
        "investment_score": p.investment_score, "diy_score": p.diy_score,
        "margin_score": p.margin_score,
        "estimated_profit_min": p.estimated_profit_min,
        "estimated_profit_max": p.estimated_profit_max,
        "estimated_roi_min": p.estimated_roi_min, "estimated_roi_max": p.estimated_roi_max,
        "estimated_renovation_cost_min": p.estimated_renovation_cost_min,
        "estimated_renovation_cost_max": p.estimated_renovation_cost_max,
        "estimated_after_renovation_value_min": p.estimated_after_renovation_value_min,
        "estimated_after_renovation_value_max": p.estimated_after_renovation_value_max,
        "renovation_level": p.renovation_level, "ai_summary": p.ai_summary,
        "first_seen": p.first_seen, "last_seen": p.last_seen, "url": p.url,
        "price_per_m2": p.price_per_m2(),
        "address": p.address, "description": p.description, "images": p.images,
        "features": p.features, "year_built": p.year_built,
        "ai_opportunities": p.ai_opportunities, "ai_risks": p.ai_risks,
        "diy_tasks": p.diy_tasks, "professional_tasks": p.professional_tasks,
        "price_score": p.price_score, "renovation_score": p.renovation_score,
        "location_score": p.location_score, "risk_score": p.risk_score,
    }
    return PropertyDetail(**data)

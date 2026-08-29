"""Deal analysis and valuation endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.models.property import Property, ComparableProperty
from backend.valuation.deal_analyzer import analyze_deal
from backend.valuation.valuation import compute_arv
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


@router.get("/properties/{property_id}/deal")
def get_deal_analysis(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Property not found")
    return analyze_deal(db, prop)


@router.get("/properties/{property_id}/valuation")
def get_valuation(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Property not found")
    return compute_arv(db, prop)


@router.get("/deals")
def list_deals(
    min_profit: Optional[float] = Query(None),
    min_roi: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_score: Optional[float] = Query(None),
    deal_status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Property).filter(Property.is_active == True)
    if max_price is not None:
        q = q.filter(Property.price <= max_price)
    if min_score is not None:
        q = q.filter(Property.investment_score >= min_score)
    if source:
        q = q.filter(Property.source == source)
    props = q.limit(limit).all()
    deals = []
    for p in props:
        d = analyze_deal(db, p)
        d["property_id"] = p.id
        d["title"] = p.title
        d["source"] = p.source
        d["postal_code"] = p.postal_code
        d["investment_score"] = p.investment_score
        if min_profit is not None and (d.get("profit_max") is None or d["profit_max"] < min_profit):
            continue
        if min_roi is not None and (d.get("roi_max") is None or d["roi_max"] < min_roi):
            continue
        if deal_status and d.get("deal_status") != deal_status:
            continue
        deals.append(d)
    order = {"STRONG DEAL": 0, "POTENTIAL DEAL": 1, "NEEDS INVESTIGATION": 2, "BAD DEAL": 3}
    deals.sort(key=lambda x: (order.get(x.get("deal_status"), 9), -(x.get("profit_max") or -1e12)))
    return deals


class ComparableIn(BaseModel):
    title: str
    price: float
    living_area: Optional[float] = None
    postal_code: Optional[str] = None
    city: Optional[str] = "Antwerpen"
    property_type: Optional[str] = "huis"
    bedrooms: Optional[int] = None
    year_built: Optional[int] = None
    epc_label: Optional[str] = None
    condition: Optional[str] = "renovated"
    url: Optional[str] = None
    source: str = "import"
    is_demo: bool = False


@router.post("/import/comparables")
def import_comparables(items: List[ComparableIn], db: Session = Depends(get_db)):
    created = 0
    for item in items:
        c = ComparableProperty(
            source=item.source, title=item.title, postal_code=item.postal_code,
            city=item.city, property_type=item.property_type, living_area=item.living_area,
            bedrooms=item.bedrooms, year_built=item.year_built, epc_label=item.epc_label,
            condition=item.condition, price=item.price, url=item.url,
            observed_at=datetime.utcnow(), is_demo=item.is_demo,
        )
        c.compute_ppm2()
        db.add(c)
        created += 1
    db.commit()
    return {"status": "ok", "created": created}


@router.get("/comparables")
def list_comparables(postal_code: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(ComparableProperty)
    if postal_code:
        q = q.filter(ComparableProperty.postal_code == postal_code)
    rows = q.limit(limit).all()
    return [{
        "id": c.id, "title": c.title, "postal_code": c.postal_code, "price": c.price,
        "living_area": c.living_area, "price_per_m2": c.price_per_m2,
        "condition": c.condition, "source": c.source, "is_demo": c.is_demo,
    } for c in rows]

"""Map endpoints — postcode centroids when exact coords unknown."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.models.property import Property
from backend.valuation.deal_analyzer import analyze_deal

router = APIRouter()

POSTCODE_CENTROIDS = {
    "2000": (51.2194, 4.4025), "2018": (51.2050, 4.4210), "2020": (51.1980, 4.3900),
    "2030": (51.2400, 4.3800), "2040": (51.3200, 4.3200), "2050": (51.2100, 4.3700),
    "2060": (51.2300, 4.4300), "2100": (51.2200, 4.4600), "2140": (51.2150, 4.4450),
    "2170": (51.2500, 4.4500), "2180": (51.2800, 4.4200), "2600": (51.1900, 4.4000),
    "2610": (51.1800, 4.3700),
}

@router.get("/map/properties")
def map_properties(
    max_price: Optional[float] = None, min_diy: Optional[float] = None,
    min_score: Optional[float] = None, source: Optional[str] = None,
    limit: int = Query(500, le=2000), db: Session = Depends(get_db),
):
    q = db.query(Property).filter(Property.is_active == True)
    if max_price is not None: q = q.filter(Property.price <= max_price)
    if min_diy is not None: q = q.filter(Property.diy_score >= min_diy)
    if min_score is not None: q = q.filter(Property.investment_score >= min_score)
    if source: q = q.filter(Property.source == source)
    features = []
    for p in q.limit(limit).all():
        lat, lng = p.latitude, p.longitude
        if lat is None or lng is None:
            centroid = POSTCODE_CENTROIDS.get(p.postal_code or "")
            if not centroid: continue
            lat, lng = centroid
            location_type = "POSTCODE_CENTROID"
        else:
            location_type = "OBSERVED"
        try:
            deal = analyze_deal(db, p)
            status = deal.get("deal_status") or "NEEDS INVESTIGATION"
            max_bid = deal.get("max_purchase_price")
            conf = deal.get("valuation_confidence")
        except Exception:
            status, max_bid, conf = "NEEDS INVESTIGATION", None, "LOW"
        features.append({
            "id": p.id, "lat": lat, "lng": lng, "location_type": location_type,
            "title": p.title, "price": p.price, "living_area": p.living_area,
            "price_per_m2": p.price_per_m2(), "deal_status": status,
            "diy_score": p.diy_score, "investment_score": p.investment_score,
            "confidence": conf, "max_bid": max_bid, "source": p.source,
            "postal_code": p.postal_code,
        })
    return {"type": "FeatureCollection", "count": len(features), "features": features}

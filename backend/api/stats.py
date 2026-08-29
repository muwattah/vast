from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.db import get_db
from backend.models.property import Property

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Property).filter(Property.is_active == True).count()
    diy = db.query(Property).filter(Property.diy_score >= 7.0, Property.is_active == True).count()
    high = db.query(Property).filter(Property.investment_score >= 8.0, Property.is_active == True).count()
    renovate = db.query(Property).filter(
        (Property.is_to_renovate == True) | (Property.is_fully_to_renovate == True),
        Property.is_active == True
    ).count()

    avg_price_m2 = db.query(
        func.avg(Property.price / Property.living_area)
    ).filter(
        Property.price.isnot(None),
        Property.living_area > 0,
        Property.is_active == True
    ).scalar()

    max_margin = db.query(func.max(Property.estimated_profit_max)).filter(
        Property.is_active == True
    ).scalar()

    return {
        "total_properties": total,
        "diy_projects": diy,
        "score_above_8": high,
        "to_renovate": renovate,
        "avg_price_per_m2": round(avg_price_m2, 0) if avg_price_m2 else None,
        "highest_estimated_margin": max_margin,
    }

"""
Seed demo data into the database (only if empty) and run analysis.
"""
from sqlalchemy.orm import Session
from backend.models.property import Property
from backend.services.demo_data import DEMO_PROPERTIES, content_hash
from backend.ai.analyzer import analyze_property, apply_analysis
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def seed_demo_data(db: Session):
    count = db.query(Property).count()
    if count > 0:
        for p in db.query(Property).filter(Property.investment_score.is_(None)).all():
            analysis = analyze_property(p)
            apply_analysis(p, analysis)
        db.commit()
        logger.info(f"Database already has {count} properties – analysis refreshed where needed.")
        return

    logger.info("Seeding demo properties...")
    for item in DEMO_PROPERTIES:
        prop = Property(
            source=item["source"],
            source_listing_id=item["source_listing_id"],
            url=item["url"],
            title=item["title"],
            price=item["price"],
            address=item.get("address"),
            postal_code=item.get("postal_code"),
            city=item.get("city"),
            district=item.get("district"),
            property_type=item.get("property_type"),
            living_area=item.get("living_area"),
            bedrooms=item.get("bedrooms"),
            bathrooms=item.get("bathrooms"),
            year_built=item.get("year_built"),
            epc_label=item.get("epc_label"),
            epc_score=item.get("epc_score"),
            description=item.get("description"),
            images=item.get("images") or [],
            features=item.get("features") or [],
            is_to_renovate=item.get("is_to_renovate", False),
            is_fully_to_renovate=item.get("is_fully_to_renovate", False),
            is_investment=item.get("is_investment", False),
            is_active=True,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            content_hash=content_hash(item),
        )
        analysis = analyze_property(prop)
        apply_analysis(prop, analysis)
        db.add(prop)
    db.commit()
    logger.info(f"Seeded and analyzed {len(DEMO_PROPERTIES)} demo properties.")

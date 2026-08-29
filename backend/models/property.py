"""
Property models for the Antwerp Real Estate Investment Platform.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from backend.database.db import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String(50), nullable=False, index=True)
    source_listing_id = Column(String(100), nullable=True, index=True)
    url = Column(String(500), nullable=False)

    title = Column(String(300), nullable=False)
    price = Column(Float, nullable=True, index=True)
    address = Column(String(300), nullable=True)
    postal_code = Column(String(10), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    property_type = Column(String(50), nullable=True, index=True)
    living_area = Column(Float, nullable=True, index=True)
    total_area = Column(Float, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)

    epc_label = Column(String(5), nullable=True, index=True)
    epc_score = Column(Float, nullable=True)
    epc_date = Column(String(30), nullable=True)

    description = Column(Text, nullable=True)
    images = Column(JSON, nullable=True)
    features = Column(JSON, nullable=True)

    is_to_renovate = Column(Boolean, default=False, index=True)
    is_fully_to_renovate = Column(Boolean, default=False)
    is_to_modernize = Column(Boolean, default=False)
    is_turnkey = Column(Boolean, default=False)
    is_casco = Column(Boolean, default=False)
    is_investment = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    content_hash = Column(String(64), nullable=True)

    ai_analyzed_at = Column(DateTime, nullable=True)
    ai_model = Column(String(80), nullable=True)
    ai_prompt_version = Column(String(20), nullable=True)

    estimated_acquisition_cost_min = Column(Float, nullable=True)
    estimated_acquisition_cost_max = Column(Float, nullable=True)
    estimated_total_investment_min = Column(Float, nullable=True)
    estimated_total_investment_max = Column(Float, nullable=True)

    diy_score = Column(Float, nullable=True, index=True)
    renovation_score = Column(Float, nullable=True)
    price_score = Column(Float, nullable=True)
    margin_score = Column(Float, nullable=True)
    location_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    investment_score = Column(Float, nullable=True, index=True)

    estimated_renovation_cost_min = Column(Float, nullable=True)
    estimated_renovation_cost_max = Column(Float, nullable=True)
    estimated_after_renovation_value_min = Column(Float, nullable=True)
    estimated_after_renovation_value_max = Column(Float, nullable=True)
    estimated_profit_min = Column(Float, nullable=True)
    estimated_profit_max = Column(Float, nullable=True)
    estimated_roi_min = Column(Float, nullable=True)
    estimated_roi_max = Column(Float, nullable=True)
    renovation_level = Column(String(30), nullable=True)

    ai_summary = Column(Text, nullable=True)
    ai_opportunities = Column(JSON, nullable=True)
    ai_risks = Column(JSON, nullable=True)
    diy_tasks = Column(JSON, nullable=True)
    professional_tasks = Column(JSON, nullable=True)

    same_property_group_id = Column(Integer, ForeignKey("same_property_groups.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "source_listing_id", name="uq_source_listing"),
        Index("ix_price_area", "price", "living_area"),
        Index("ix_investment_score", "investment_score"),
    )

    def price_per_m2(self) -> Optional[float]:
        if self.price and self.living_area and self.living_area > 0:
            return round(self.price / self.living_area, 0)
        return None


class SamePropertyGroup(Base):
    __tablename__ = "same_property_groups"
    id = Column(Integer, primary_key=True)
    canonical_title = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    properties = relationship("Property", backref="same_group")


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    property = relationship("Property")

"""Pydantic schemas for validated AI analysis output."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AnalysisResult(BaseModel):
    diy_score: float = Field(ge=1, le=10)
    renovation_score: float = Field(ge=1, le=10)
    price_score: float = Field(ge=1, le=10)
    margin_score: float = Field(ge=1, le=10)
    location_score: float = Field(ge=1, le=10)
    risk_score: float = Field(ge=1, le=10)
    investment_score: float = Field(ge=1, le=10)

    estimated_renovation_cost_min: float
    estimated_renovation_cost_max: float
    estimated_after_renovation_value_min: float
    estimated_after_renovation_value_max: float
    estimated_acquisition_cost_min: float = 0
    estimated_acquisition_cost_max: float = 0
    estimated_total_investment_min: float = 0
    estimated_total_investment_max: float = 0
    estimated_profit_min: float
    estimated_profit_max: float
    roi_min: float
    roi_max: float

    renovation_level: str
    diy_tasks: List[str] = []
    professional_tasks: List[str] = []
    opportunities: List[str] = []
    risks: List[str] = []
    summary: str = ""
    uncertainty_notes: List[str] = []

    @field_validator("renovation_level")
    @classmethod
    def level_ok(cls, v):
        if v not in ("light", "medium", "heavy"):
            return "medium"
        return v

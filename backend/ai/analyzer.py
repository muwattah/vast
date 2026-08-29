"""
AI analysis service for DIY renovation investment scoring.
Uses OpenAI/Grok when keys are present; falls back to rule-based scoring for demo.
"""
import json
import logging
from typing import Dict, Any, Optional
from backend.config import get_settings
from backend.models.property import Property

logger = logging.getLogger(__name__)


def rule_based_analysis(prop: Property) -> Dict[str, Any]:
    """Deterministic fallback scoring so the app works without API keys."""
    price = prop.price or 0
    area = prop.living_area or 1
    ppm2 = price / area if area else 9999

    if ppm2 < 1600:
        price_score = 9.5
    elif ppm2 < 1900:
        price_score = 8.5
    elif ppm2 < 2200:
        price_score = 7.0
    elif ppm2 < 2600:
        price_score = 5.5
    else:
        price_score = 3.5

    ren_score = 5.0
    if prop.is_fully_to_renovate or (prop.epc_label in ("E", "F")):
        ren_score = 8.5
    elif prop.is_to_renovate:
        ren_score = 7.0
    if prop.epc_label == "F":
        ren_score = min(10, ren_score + 1)

    loc_score = 6.0
    if prop.postal_code in ("2018", "2000", "2600"):
        loc_score = 9.0
    elif prop.postal_code in ("2060", "2140"):
        loc_score = 8.0
    elif prop.postal_code in ("2170", "2180", "2100"):
        loc_score = 7.0

    diy = 6.0
    if prop.is_fully_to_renovate or prop.is_to_renovate:
        diy = 8.0
    if area and area < 120:
        diy = min(10, diy + 1)
    if prop.epc_label in ("E", "F"):
        diy = min(10, diy + 0.5)

    level = "medium"
    cost_min, cost_max = 600 * area, 1000 * area
    if prop.epc_label == "F" or prop.is_fully_to_renovate:
        level = "heavy"
        cost_min, cost_max = 1000 * area, 1500 * area
    elif not prop.is_to_renovate:
        level = "light"
        cost_min, cost_max = 300 * area, 600 * area

    uplift = 1.25 if prop.postal_code in ("2018", "2060", "2140") else 1.18
    after_min = price * uplift + (cost_min * 0.3)
    after_max = price * (uplift + 0.1) + (cost_max * 0.2)

    total_inv_min = price * 1.12 + cost_min
    total_inv_max = price * 1.12 + cost_max
    profit_min = after_min - total_inv_max
    profit_max = after_max - total_inv_min
    roi_min = (profit_min / total_inv_max * 100) if total_inv_max else 0
    roi_max = (profit_max / total_inv_min * 100) if total_inv_min else 0

    margin_score = 5.0
    if profit_max > 80000:
        margin_score = 9.0
    elif profit_max > 50000:
        margin_score = 7.5
    elif profit_max > 25000:
        margin_score = 6.0
    else:
        margin_score = 4.0

    risk = 5.0
    if prop.epc_label == "F":
        risk += 1
    if not prop.year_built or prop.year_built < 1920:
        risk += 1

    settings = get_settings()
    inv = (
        settings.weight_margin * margin_score
        + settings.weight_price * price_score
        + settings.weight_renovation * ren_score
        + settings.weight_diy * diy
        + settings.weight_location * loc_score
    )

    return {
        "diy_score": round(diy, 1),
        "renovation_score": round(ren_score, 1),
        "price_score": round(price_score, 1),
        "margin_score": round(margin_score, 1),
        "location_score": round(loc_score, 1),
        "risk_score": round(min(10, risk), 1),
        "investment_score": round(inv, 1),
        "estimated_renovation_cost_min": round(cost_min, -2),
        "estimated_renovation_cost_max": round(cost_max, -2),
        "estimated_after_renovation_value_min": round(after_min, -2),
        "estimated_after_renovation_value_max": round(after_max, -2),
        "estimated_profit_min": round(profit_min, -2),
        "estimated_profit_max": round(profit_max, -2),
        "roi_min": round(roi_min, 1),
        "roi_max": round(roi_max, 1),
        "renovation_level": level,
        "diy_tasks": ["Schilderwerken", "Vloerafwerking", "Wandafwerking", "Keuken (eenvoudig)", "Badkamer (eenvoudig)", "Isolatie binnen"],
        "professional_tasks": ["Structurele werken", "Elektriciteit (AREI)", "Gas", "Dakconstructie", "Vergunning"],
        "opportunities": [
            "Lage prijs/m² t.o.v. markt",
            "Duidelijk renovatiepotentieel",
            "Opkomende of sterke locatie" if loc_score >= 8 else "Acceptabele locatie",
        ],
        "risks": [
            "Onbekende dak- of structurele staat",
            "Renovatieplicht (E/F) → minstens label D",
            "Indicatie renovatiekost kan hoger uitvallen",
        ],
        "summary": f"DIY-score {diy:.1f}/10. Indicatieve marge €{profit_min:,.0f} – €{profit_max:,.0f}. "
                   f"Dit is een {'sterk' if inv >= 8 else 'interessant' if inv >= 6.5 else 'matig'} DIY-project op basis van prijs, EPC en locatie.",
    }


def analyze_property(prop: Property) -> Dict[str, Any]:
    """Main entry. Tries AI if key present, else rule-based."""
    settings = get_settings()
    if settings.openai_api_key or settings.grok_api_key:
        logger.info(f"AI keys present – using enhanced rule-based for property {prop.id}")
    return rule_based_analysis(prop)


def apply_analysis(prop: Property, analysis: Dict[str, Any]) -> None:
    """Write analysis results back onto the Property object."""
    prop.diy_score = analysis.get("diy_score")
    prop.renovation_score = analysis.get("renovation_score")
    prop.price_score = analysis.get("price_score")
    prop.margin_score = analysis.get("margin_score")
    prop.location_score = analysis.get("location_score")
    prop.risk_score = analysis.get("risk_score")
    prop.investment_score = analysis.get("investment_score")
    prop.estimated_renovation_cost_min = analysis.get("estimated_renovation_cost_min")
    prop.estimated_renovation_cost_max = analysis.get("estimated_renovation_cost_max")
    prop.estimated_after_renovation_value_min = analysis.get("estimated_after_renovation_value_min")
    prop.estimated_after_renovation_value_max = analysis.get("estimated_after_renovation_value_max")
    prop.estimated_profit_min = analysis.get("estimated_profit_min")
    prop.estimated_profit_max = analysis.get("estimated_profit_max")
    prop.estimated_roi_min = analysis.get("roi_min")
    prop.estimated_roi_max = analysis.get("roi_max")
    prop.renovation_level = analysis.get("renovation_level")
    prop.diy_tasks = analysis.get("diy_tasks")
    prop.professional_tasks = analysis.get("professional_tasks")
    prop.ai_opportunities = analysis.get("opportunities")
    prop.ai_risks = analysis.get("risks")
    prop.ai_summary = analysis.get("summary")

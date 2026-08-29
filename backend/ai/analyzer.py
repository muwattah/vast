"""
Investment analysis engine.
Uses AI providers when keys present; always falls back to transparent rule-based model.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from backend.config import get_settings
from backend.models.property import Property
from backend.ai.schemas import AnalysisResult
from backend.ai.prompts import PROMPT_VERSION
from backend.ai.providers.openai import OpenAIProvider
from backend.ai.providers.grok import GrokProvider

logger = logging.getLogger(__name__)


def _acquisition_cost_range(price: float) -> tuple:
    """Indicative Flanders acquisition costs (~8-12%). NOT legal/tax advice."""
    if not price or price <= 0:
        return 0.0, 0.0
    return round(price * 0.08, -2), round(price * 0.12, -2)


def rule_based_analysis(prop: Property) -> Dict[str, Any]:
    price = float(prop.price or 0)
    area = float(prop.living_area or 1)
    ppm2 = price / area if area else 9999.0

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
        ren_score = min(10.0, ren_score + 1)

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
        diy = min(10.0, diy + 1)
    if prop.epc_label in ("E", "F"):
        diy = min(10.0, diy + 0.5)

    settings = get_settings()
    if prop.epc_label == "F" or prop.is_fully_to_renovate:
        level = "heavy"
        cost_min = settings.renovation_cost_heavy_min * area
        cost_max = settings.renovation_cost_heavy_max * area
    elif prop.is_to_renovate or prop.epc_label == "E":
        level = "medium"
        cost_min = settings.renovation_cost_medium_min * area
        cost_max = settings.renovation_cost_medium_max * area
    else:
        level = "light"
        cost_min = settings.renovation_cost_light_min * area
        cost_max = settings.renovation_cost_light_max * area

    acq_min, acq_max = _acquisition_cost_range(price)

    if prop.postal_code in ("2018", "2060", "2140", "2000"):
        uplift_min, uplift_max = 1.15, 1.30
    else:
        uplift_min, uplift_max = 1.10, 1.22

    after_min = price * uplift_min
    after_max = price * uplift_max + cost_max * 0.15

    total_inv_min = price + acq_min + cost_min
    total_inv_max = price + acq_max + cost_max
    profit_min = after_min - total_inv_max
    profit_max = after_max - total_inv_min
    roi_min = (profit_min / total_inv_max * 100) if total_inv_max else 0
    roi_max = (profit_max / total_inv_min * 100) if total_inv_min else 0

    if profit_max > 80000:
        margin_score = 9.0
    elif profit_max > 40000:
        margin_score = 7.0
    elif profit_max > 15000:
        margin_score = 5.5
    else:
        margin_score = 3.5

    risk = 5.0
    if prop.epc_label == "F":
        risk += 1.5
    if not prop.year_built or (prop.year_built and prop.year_built < 1920):
        risk += 1
    if not prop.living_area:
        risk += 1
    risk = min(10.0, risk)

    inv = (
        settings.weight_margin * margin_score
        + settings.weight_price * price_score
        + settings.weight_renovation * ren_score
        + settings.weight_diy * diy
        + settings.weight_location * loc_score
    )

    uncertainty = [
        "After-renovation value is an estimate without live comparable sales data.",
        "Acquisition costs are indicative (Flanders typical band); actual rates depend on buyer situation.",
        "Renovation cost ranges are EUR/m2 heuristics and can vary by condition and finish level.",
    ]

    return {
        "diy_score": round(diy, 1),
        "renovation_score": round(ren_score, 1),
        "price_score": round(price_score, 1),
        "margin_score": round(margin_score, 1),
        "location_score": round(loc_score, 1),
        "risk_score": round(risk, 1),
        "investment_score": round(inv, 1),
        "estimated_renovation_cost_min": round(cost_min, -2),
        "estimated_renovation_cost_max": round(cost_max, -2),
        "estimated_after_renovation_value_min": round(after_min, -2),
        "estimated_after_renovation_value_max": round(after_max, -2),
        "estimated_acquisition_cost_min": acq_min,
        "estimated_acquisition_cost_max": acq_max,
        "estimated_total_investment_min": round(total_inv_min, -2),
        "estimated_total_investment_max": round(total_inv_max, -2),
        "estimated_profit_min": round(profit_min, -2),
        "estimated_profit_max": round(profit_max, -2),
        "roi_min": round(roi_min, 1),
        "roi_max": round(roi_max, 1),
        "renovation_level": level,
        "diy_tasks": ["Schilderwerken", "Vloerafwerking", "Wandafwerking / gyproc", "Keuken (eenvoudig)", "Badkamer (eenvoudig)", "Isolatie langs binnen"],
        "professional_tasks": ["Structurele werken", "Elektriciteit (AREI)", "Gas / stookinstallatie", "Dakconstructie", "Vergunning / stedenbouw"],
        "opportunities": [
            "Lage of aantrekkelijke prijs/m2" if price_score >= 7 else "Prijs in lijn met of boven ruwe marktband",
            "Duidelijk renovatiepotentieel" if ren_score >= 7 else "Beperkt renovatiepotentieel zichtbaar",
            "Sterke of opkomende locatie" if loc_score >= 8 else "Acceptabele locatie",
        ],
        "risks": [
            "Onbekende dak- of structurele staat",
            "Renovatieplicht (E/F) -> minstens label D binnen termijn",
            "Indicatie renovatiekost kan hoger uitvallen bij onvoorziene werken",
        ],
        "summary": (
            f"DIY-score {diy:.1f}/10. Indicatieve totale investering "
            f"EUR {total_inv_min:,.0f} - EUR {total_inv_max:,.0f}. "
            f"Geschatte bruto marge EUR {profit_min:,.0f} - EUR {profit_max:,.0f}. "
            f"{'Interessant' if inv >= 6.5 else 'Matig'} DIY-project. Waarden zijn schattingen zonder live comparables."
        ),
        "uncertainty_notes": uncertainty,
        "_ai_model": "rule-based",
        "_prompt_version": PROMPT_VERSION,
    }


def analyze_property(prop: Property) -> Dict[str, Any]:
    settings = get_settings()
    prop_data = {
        "title": prop.title, "price": prop.price, "living_area": prop.living_area,
        "postal_code": prop.postal_code, "district": prop.district,
        "property_type": prop.property_type, "epc_label": prop.epc_label,
        "epc_score": prop.epc_score, "bedrooms": prop.bedrooms,
        "year_built": prop.year_built, "is_to_renovate": prop.is_to_renovate,
        "is_fully_to_renovate": prop.is_fully_to_renovate,
        "is_investment": prop.is_investment, "description": prop.description,
    }
    providers = []
    if settings.openai_api_key:
        providers.append(OpenAIProvider())
    if settings.grok_api_key:
        providers.append(GrokProvider())
    for provider in providers:
        result = provider.analyze(prop_data)
        if result:
            data = result.model_dump()
            data["_ai_model"] = provider.name
            data["_prompt_version"] = PROMPT_VERSION
            logger.info(f"AI analysis via {provider.name} for property {prop.id}")
            return data
    return rule_based_analysis(prop)


def apply_analysis(prop: Property, analysis: Dict[str, Any]) -> None:
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
    prop.estimated_acquisition_cost_min = analysis.get("estimated_acquisition_cost_min")
    prop.estimated_acquisition_cost_max = analysis.get("estimated_acquisition_cost_max")
    prop.estimated_total_investment_min = analysis.get("estimated_total_investment_min")
    prop.estimated_total_investment_max = analysis.get("estimated_total_investment_max")
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
    prop.ai_analyzed_at = datetime.utcnow()
    prop.ai_model = analysis.get("_ai_model", "rule-based")
    prop.ai_prompt_version = analysis.get("_prompt_version", PROMPT_VERSION)

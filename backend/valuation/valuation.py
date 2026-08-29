"""ARV engine — uses ONLY stored comparables, never invents prices."""
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.models.property import Property
from backend.valuation.comparable import find_comparables
from backend.valuation.adjustments import adjustment_per_m2
from backend.valuation.confidence import valuation_confidence
import statistics


def compute_arv(db: Session, prop: Property) -> Dict[str, Any]:
    matches = find_comparables(db, prop, min_similarity=70.0, limit=15)
    result = {
        "arv_low": None, "arv_median": None, "arv_high": None,
        "confidence": "LOW", "comparable_count": len(matches),
        "median_ppm2": None,
        "subject_ppm2": prop.price_per_m2() if prop.price and prop.living_area else None,
        "comparables": [], "data_quality": "INSUFFICIENT", "notes": [],
    }
    if not matches:
        result["notes"].append("Onvoldoende vergelijkingsdata (geen comparables met similarity >= 70%).")
        return result
    ppm2_list = []
    for comp, sim in matches:
        ppm2 = comp.price_per_m2 or (comp.price / comp.living_area if comp.living_area else None)
        if not ppm2:
            continue
        renovated_ppm2 = ppm2 - adjustment_per_m2(comp.condition)
        ppm2_list.append(renovated_ppm2)
        result["comparables"].append({
            "id": comp.id, "title": comp.title, "postal_code": comp.postal_code,
            "living_area": comp.living_area, "price": comp.price, "price_per_m2": ppm2,
            "condition": comp.condition, "similarity": sim, "source": comp.source,
            "is_demo": comp.is_demo, "url": comp.url,
            "observed_at": comp.observed_at.isoformat() if comp.observed_at else None,
        })
    if not ppm2_list or not prop.living_area:
        result["notes"].append("Geen bruikbare EUR/m2 of ontbrekende oppervlakte.")
        return result
    ppm2_list.sort()
    med = statistics.median(ppm2_list)
    if len(ppm2_list) >= 3:
        low_p = ppm2_list[max(0, int(len(ppm2_list) * 0.25))]
        high_p = ppm2_list[min(len(ppm2_list) - 1, int(len(ppm2_list) * 0.75))]
    else:
        low_p, high_p = min(ppm2_list), max(ppm2_list)
    area = prop.living_area
    result["median_ppm2"] = round(med, 0)
    result["arv_low"] = round(low_p * area, -2)
    result["arv_median"] = round(med * area, -2)
    result["arv_high"] = round(high_p * area, -2)
    result["confidence"] = valuation_confidence(matches, prop.living_area)
    result["data_quality"] = "OBSERVED_COMPARABLES"
    result["notes"].append(f"Gebaseerd op {len(matches)} comparable(s) met similarity >= 70%.")
    if any(c.is_demo for c, _ in matches):
        result["notes"].append("Let op: een of meer comparables zijn DEMO-data.")
    return result

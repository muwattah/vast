"""Human-readable WHY explanations — rule-based."""
from typing import Dict, Any, List
from backend.models.property import Property

def explain_deal(prop: Property, deal: Dict[str, Any]) -> Dict[str, Any]:
    reasons_pos: List[str] = []
    reasons_neg: List[str] = []
    risks: List[str] = []
    ppm2 = deal.get("subject_ppm2")
    med = deal.get("median_comp_ppm2")
    if ppm2 and med and ppm2 < med * 0.85:
        reasons_pos.append(f"Low purchase EUR/m2 ({ppm2:.0f}) vs comparable median ({med:.0f})")
    elif ppm2 and med and ppm2 > med * 1.1:
        reasons_neg.append(f"Purchase EUR/m2 ({ppm2:.0f}) above comparable median ({med:.0f})")
    if prop.diy_score and prop.diy_score >= 8:
        reasons_pos.append("Large DIY upside (DIY score >= 8)")
    if deal.get("comparable_count", 0) >= 3:
        reasons_pos.append(f"Comparable evidence ({deal['comparable_count']} comps, confidence {deal.get('valuation_confidence')})")
    elif deal.get("comparable_count", 0) == 0:
        reasons_neg.append("No comparable data — ARV unreliable")
        risks.append("Insufficient market evidence")
    if prop.epc_label in ("E", "F"):
        risks.append(f"EPC {prop.epc_label} — renovatieplicht risk")
    if prop.is_fully_to_renovate:
        risks.append("Fully to renovate — possible structural works")
    risks.append("Electrical condition unknown")
    risks.append("Asbestos status unknown")
    over = deal.get("over_asking")
    if over is not None and over > 0:
        reasons_neg.append(f"Asking price above max bid by EUR {over:,.0f}")
    elif over is not None and over <= 0:
        reasons_pos.append("Asking within or below max bid")
    conf_map = {"HIGH": 82, "MEDIUM": 55, "LOW": 30}
    conf_pct = conf_map.get(deal.get("valuation_confidence") or "LOW", 30)
    return {
        "why_positive": reasons_pos, "why_negative": reasons_neg, "risks": risks,
        "confidence_pct": conf_pct,
        "confidence_basis": f"{deal.get('comparable_count') or 0} comparables, confidence {deal.get('valuation_confidence')}",
        "deal_status": deal.get("deal_status"),
    }

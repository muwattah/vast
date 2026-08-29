"""Deal analysis: total investment, profit, ROI, max purchase price, deal status."""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.property import Property
from backend.config import get_settings
from backend.valuation.valuation import compute_arv


def diy_renovation_range(market_min, market_max):
    s = get_settings()
    f = s.diy_cost_factor
    return round(market_min * f, -2), round(market_max * f, -2)


def contingency_on(amount_min, amount_max):
    s = get_settings()
    c = s.renovation_contingency
    return round(amount_min * c, -2), round(amount_max * c, -2)


def deal_status(profit_max, roi_max, confidence, asking, max_buy, diy_score, risk_score):
    if confidence == "LOW" and (profit_max is None or profit_max < 0):
        return "NEEDS INVESTIGATION"
    if max_buy is not None and asking is not None and asking > max_buy * 1.15:
        return "BAD DEAL"
    if profit_max is not None and profit_max < 0 and (roi_max is None or roi_max < 5):
        return "BAD DEAL"
    if (confidence in ("MEDIUM", "HIGH") and profit_max is not None and profit_max >= 50000
            and roi_max is not None and roi_max >= 15
            and (diy_score is None or diy_score >= 7)
            and (max_buy is None or asking is None or asking <= max_buy * 1.05)):
        return "STRONG DEAL"
    if profit_max is not None and profit_max >= 20000 and (roi_max is None or roi_max >= 8):
        return "POTENTIAL DEAL"
    if confidence == "LOW":
        return "NEEDS INVESTIGATION"
    return "POTENTIAL DEAL"


def max_purchase_price(arv_median, reno_max, acq_rate_max=0.12, other_costs=0,
                       target_roi=None, minimum_profit=None):
    if arv_median is None or arv_median <= 0:
        return None
    s = get_settings()
    target_roi = target_roi if target_roi is not None else s.target_roi
    minimum_profit = minimum_profit if minimum_profit is not None else s.minimum_profit
    lo, hi = 0.0, float(arv_median)
    best = None
    for _ in range(40):
        mid = (lo + hi) / 2
        total = mid * (1 + acq_rate_max) + reno_max + other_costs
        profit = arv_median - total
        roi = profit / total if total > 0 else -1
        if profit >= minimum_profit and roi >= target_roi:
            best = mid
            lo = mid
        else:
            hi = mid
    return round(best, -2) if best is not None else None


def analyze_deal(db: Session, prop: Property) -> Dict[str, Any]:
    settings = get_settings()
    arv = compute_arv(db, prop)
    price = float(prop.price or 0)
    reno_min = float(prop.estimated_renovation_cost_min or 0)
    reno_max = float(prop.estimated_renovation_cost_max or 0)
    if reno_min == 0 and reno_max == 0 and prop.living_area:
        area = prop.living_area
        reno_min = settings.renovation_cost_medium_min * area
        reno_max = settings.renovation_cost_medium_max * area
    diy_min, diy_max = diy_renovation_range(reno_min, reno_max)
    cont_min, cont_max = contingency_on(diy_min, diy_max)
    acq_min = float(prop.estimated_acquisition_cost_min or round(price * 0.08, -2))
    acq_max = float(prop.estimated_acquisition_cost_max or round(price * 0.12, -2))
    total_min = price + acq_min + diy_min + cont_min
    total_max = price + acq_max + diy_max + cont_max
    arv_low, arv_med, arv_high = arv.get("arv_low"), arv.get("arv_median"), arv.get("arv_high")
    profit_min = (arv_low - total_max) if arv_low is not None else None
    profit_max = (arv_high - total_min) if arv_high is not None else None
    roi_min = (profit_min / total_max * 100) if profit_min is not None and total_max else None
    roi_max = (profit_max / total_min * 100) if profit_max is not None and total_min else None
    max_buy = max_purchase_price(arv_med, reno_max=diy_max + cont_max)
    over_asking = round(price - max_buy, -2) if max_buy is not None and price else None
    status = deal_status(profit_max, roi_max, arv.get("confidence", "LOW"), price or None, max_buy, prop.diy_score, prop.risk_score)
    return {
        "asking_price": price or None,
        "subject_ppm2": arv.get("subject_ppm2"),
        "median_comp_ppm2": arv.get("median_ppm2"),
        "market_renovation_min": round(reno_min, -2),
        "market_renovation_max": round(reno_max, -2),
        "diy_renovation_min": diy_min, "diy_renovation_max": diy_max,
        "contingency_min": cont_min, "contingency_max": cont_max,
        "contingency_pct": settings.renovation_contingency,
        "acquisition_min": acq_min, "acquisition_max": acq_max,
        "total_investment_min": round(total_min, -2),
        "total_investment_max": round(total_max, -2),
        "arv_low": arv_low, "arv_median": arv_med, "arv_high": arv_high,
        "valuation_confidence": arv.get("confidence"),
        "comparable_count": arv.get("comparable_count"),
        "comparables": arv.get("comparables"),
        "valuation_notes": arv.get("notes"),
        "profit_min": round(profit_min, -2) if profit_min is not None else None,
        "profit_max": round(profit_max, -2) if profit_max is not None else None,
        "roi_min": round(roi_min, 1) if roi_min is not None else None,
        "roi_max": round(roi_max, 1) if roi_max is not None else None,
        "max_purchase_price": max_buy, "over_asking": over_asking,
        "target_roi": settings.target_roi, "minimum_profit": settings.minimum_profit,
        "deal_status": status,
        "diy_tasks": prop.diy_tasks, "professional_tasks": prop.professional_tasks,
        "diy_score": prop.diy_score, "risk_score": prop.risk_score,
        "data_labels": {
            "asking_price": "OBSERVED",
            "arv": "ESTIMATED" if arv_med else "UNKNOWN",
            "renovation": "ESTIMATED",
            "acquisition": "ASSUMPTION",
            "contingency": "ASSUMPTION",
        },
    }

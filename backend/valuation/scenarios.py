"""Conservative / Base / Optimistic investor scenarios + worst-case."""
from sqlalchemy.orm import Session
from backend.models.property import Property
from backend.valuation.deal_analyzer import analyze_deal, max_purchase_price
from backend.config import get_settings

def build_scenarios(db: Session, prop: Property):
    deal = analyze_deal(db, prop)
    price = float(prop.price or 0)
    settings = get_settings()
    diy_min = deal.get("diy_renovation_min") or 0
    diy_max = deal.get("diy_renovation_max") or 0
    diy_med = (diy_min + diy_max) / 2 if diy_min and diy_max else 0
    arv_low, arv_med, arv_high = deal.get("arv_low"), deal.get("arv_median"), deal.get("arv_high")
    acq_min = deal.get("acquisition_min") or price * 0.08
    acq_max = deal.get("acquisition_max") or price * 0.12
    acq_med = (acq_min + acq_max) / 2
    cont_pct_base = settings.renovation_contingency
    cont_pct_high = max(cont_pct_base, 0.15)

    def scenario(label, arv, reno, cont_pct, acq):
        if arv is None:
            return {"label": label, "available": False, "reason": "ARV onvoldoende gegevens"}
        cont = reno * cont_pct
        total = price + acq + reno + cont
        profit = arv - total
        roi = (profit / total * 100) if total else 0
        max_bid = max_purchase_price(arv, reno_max=reno + cont, acq_rate_max=0.12)
        return {
            "label": label, "available": True, "purchase": price,
            "acquisition": round(acq, -2), "renovation": round(reno, -2),
            "contingency": round(cont, -2), "contingency_pct": cont_pct,
            "total_investment": round(total, -2),
            "arv": round(arv, -2) if arv else None,
            "profit": round(profit, -2), "roi_pct": round(roi, 1), "max_bid": max_bid,
        }

    conservative = scenario("CONSERVATIVE", arv_low, diy_max, cont_pct_high, acq_max)
    base = scenario("BASE", arv_med, diy_med, cont_pct_base, acq_med)
    optimistic = scenario("OPTIMISTIC", arv_high, diy_min, cont_pct_base, acq_min)
    worst = scenario("WORST_CASE", arv_low, diy_max, cont_pct_high, acq_max)
    if worst.get("available") and worst.get("profit", -1) > 0:
        outlook = "STRONG"
    elif base.get("available") and base.get("profit", -1) > 0:
        outlook = "BASE_POSITIVE"
    elif optimistic.get("available") and optimistic.get("profit", -1) > 0:
        outlook = "SPECULATIVE"
    else:
        outlook = "NEGATIVE"
    return {
        "conservative": conservative, "base": base, "optimistic": optimistic,
        "worst_case": worst, "outlook": outlook,
        "valuation_confidence": deal.get("valuation_confidence"),
        "comparable_count": deal.get("comparable_count"),
        "data_note": "DEMO comparables marked as such; ARV requires observed comps.",
    }

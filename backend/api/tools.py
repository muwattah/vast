"""Investor tools: max bid, scenario calculator, compare, completeness, risk flags."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database.db import get_db
from backend.models.property import Property
from backend.valuation.deal_analyzer import max_purchase_price, analyze_deal

router = APIRouter()


class MaxBidRequest(BaseModel):
    arv: float
    renovation_budget: float
    contingency_pct: float = 0.10
    acquisition_rate: float = 0.12
    other_costs: float = 0
    desired_profit: Optional[float] = None
    target_roi: Optional[float] = None


@router.post("/tools/max-bid")
def calc_max_bid(body: MaxBidRequest):
    reno = body.renovation_budget * (1 + body.contingency_pct)
    mp = max_purchase_price(
        arv_median=body.arv, reno_max=reno, acq_rate_max=body.acquisition_rate,
        other_costs=body.other_costs, target_roi=body.target_roi,
        minimum_profit=body.desired_profit,
    )
    return {
        "arv": body.arv, "effective_renovation": round(reno, -2), "max_bid": mp,
        "assumptions": {
            "contingency_pct": body.contingency_pct, "acquisition_rate": body.acquisition_rate,
            "other_costs": body.other_costs, "desired_profit": body.desired_profit,
            "target_roi": body.target_roi,
        },
    }


class ScenarioRequest(BaseModel):
    purchase_price: float
    renovation_budget: float
    contingency_pct: float = 0.10
    acquisition_rate: float = 0.10
    other_costs: float = 0
    arv: float
    desired_profit: Optional[float] = None
    target_roi: Optional[float] = None


@router.post("/tools/scenario")
def scenario_calculator(body: ScenarioRequest):
    acq = body.purchase_price * body.acquisition_rate
    cont = body.renovation_budget * body.contingency_pct
    total = body.purchase_price + acq + body.renovation_budget + cont + body.other_costs
    profit = body.arv - total
    roi = (profit / total * 100) if total else 0
    mp = max_purchase_price(
        body.arv, reno_max=body.renovation_budget + cont, acq_rate_max=body.acquisition_rate,
        other_costs=body.other_costs, target_roi=body.target_roi, minimum_profit=body.desired_profit,
    )
    over = round(body.purchase_price - mp, -2) if mp is not None else None
    if profit >= 50000 and roi >= 15 and (mp is None or body.purchase_price <= (mp or 0) * 1.05):
        status = "STRONG DEAL"
    elif profit >= 20000 and roi >= 8:
        status = "POTENTIAL DEAL"
    elif profit < 0:
        status = "BAD DEAL"
    else:
        status = "NEEDS INVESTIGATION"
    return {
        "total_investment": round(total, -2), "acquisition_cost": round(acq, -2),
        "contingency": round(cont, -2), "profit": round(profit, -2),
        "roi_pct": round(roi, 1), "max_bid": mp, "over_asking": over, "deal_status": status,
    }


@router.get("/tools/compare")
def compare_properties(ids: str = Query(...), db: Session = Depends(get_db)):
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()][:4]
    if len(id_list) < 2:
        raise HTTPException(400, "Provide at least 2 property ids")
    rows = []
    for pid in id_list:
        p = db.query(Property).filter(Property.id == pid).first()
        if not p:
            continue
        d = analyze_deal(db, p)
        rows.append({
            "id": p.id, "title": p.title, "source": p.source, "asking_price": p.price,
            "living_area": p.living_area, "price_per_m2": p.price_per_m2(),
            "epc_label": p.epc_label, "diy_score": p.diy_score,
            "investment_score": p.investment_score, "arv_median": d.get("arv_median"),
            "total_investment_max": d.get("total_investment_max"),
            "profit_max": d.get("profit_max"), "roi_max": d.get("roi_max"),
            "max_purchase_price": d.get("max_purchase_price"),
            "valuation_confidence": d.get("valuation_confidence"),
            "deal_status": d.get("deal_status"), "diy_renovation_max": d.get("diy_renovation_max"),
        })
    def best_key(key, higher=True):
        vals = [(r["id"], r.get(key)) for r in rows if r.get(key) is not None]
        if not vals:
            return None
        return (max if higher else min)(vals, key=lambda x: x[1])[0]
    best = {
        "lowest_asking": best_key("asking_price", higher=False),
        "lowest_ppm2": best_key("price_per_m2", higher=False),
        "highest_diy": best_key("diy_score"),
        "highest_profit": best_key("profit_max"),
        "highest_roi": best_key("roi_max"),
        "highest_max_bid": best_key("max_purchase_price"),
    }
    return {"properties": rows, "best": best}


def completeness_score(prop: Property) -> int:
    fields = [prop.price, prop.living_area, prop.epc_label, prop.postal_code,
              prop.description, prop.bedrooms, prop.property_type, prop.year_built,
              prop.address, prop.images]
    filled = sum(1 for f in fields if f not in (None, "", [], {}))
    return round(filled / len(fields) * 100)


def risk_flags(prop: Property) -> List[str]:
    flags = []
    if not prop.epc_label:
        flags.append("Missing EPC")
    elif prop.epc_label in ("E", "F"):
        flags.append(f"EPC {prop.epc_label} – renovatieplicht risico")
    if prop.is_fully_to_renovate:
        flags.append("Possible structural renovation")
    if not prop.year_built:
        flags.append("Unknown construction year")
    flags.append("Unknown electrical condition")
    flags.append("Unknown asbestos status")
    flags.append("Permit information unavailable")
    if not prop.description or len(prop.description) < 50:
        flags.append("Limited listing description")
    return flags


@router.get("/properties/{property_id}/quality")
def property_quality(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Not found")
    return {
        "completeness": completeness_score(prop),
        "risk_flags": risk_flags(prop),
        "data_labels": {
            "price": "OBSERVED" if prop.price else "UNKNOWN",
            "price_per_m2": "CALCULATED" if prop.price and prop.living_area else "UNKNOWN",
            "epc": "OBSERVED" if prop.epc_label else "UNKNOWN",
            "arv": "ESTIMATED", "renovation": "ESTIMATED",
        },
    }

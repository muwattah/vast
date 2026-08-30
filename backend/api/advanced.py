"""Import preview, scenarios, offer analysis, due diligence, deal quality, market data."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json
from backend.database.db import get_db
from backend.models.property import Property, DueDiligenceItem, ComparableProperty
from backend.importers.preview import preview_import
from backend.importers.service import upsert_properties
from backend.valuation.scenarios import build_scenarios
from backend.valuation.deal_analyzer import max_purchase_price, analyze_deal
from backend.valuation.outliers import detect_ppm2_outliers

router = APIRouter()
DD_ITEMS = ["epc","asbestos","electricity","roof","moisture","heating","windows","sewage","urban_planning","permits","soil","syndic_docs","site_visit"]

@router.post("/import/preview")
async def import_preview(file: UploadFile = File(...), mapping_json: Optional[str] = Form(None)):
    content = await file.read()
    kind = "csv" if (file.filename or "").lower().endswith(".csv") else "json"
    mapping = json.loads(mapping_json) if mapping_json else None
    result = preview_import(content, kind=kind, mapping=mapping, filename=file.filename or "")
    result.pop("items", None)
    return result

@router.post("/import/confirm")
async def import_confirm(file: UploadFile = File(...), mapping_json: Optional[str] = Form(None), db: Session = Depends(get_db)):
    content = await file.read()
    kind = "csv" if (file.filename or "").lower().endswith(".csv") else "json"
    mapping = json.loads(mapping_json) if mapping_json else None
    result = preview_import(content, kind=kind, mapping=mapping, filename=file.filename or "")
    items = result.get("items") or []
    if not items:
        raise HTTPException(400, "No valid rows to import")
    stats = upsert_properties(db, items, run_analysis=True)
    return {"status": "ok", "rows_found": result["rows_found"], "valid": result["valid"],
            "invalid": result["invalid"], "imported": stats,
            "errors": result["errors"][:20], "warnings": result["warnings"][:20]}

@router.get("/properties/{property_id}/scenarios")
def property_scenarios(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop: raise HTTPException(404, "Not found")
    return build_scenarios(db, prop)

class OfferIn(BaseModel):
    asking_price: float
    my_offer: float
    arv: Optional[float] = None
    renovation_budget: Optional[float] = None
    contingency_pct: float = 0.10
    acquisition_rate: float = 0.12
    desired_profit: Optional[float] = None
    target_roi: Optional[float] = None

@router.post("/tools/offer")
def offer_analysis(body: OfferIn):
    discount = (body.asking_price - body.my_offer) / body.asking_price * 100 if body.asking_price else 0
    max_bid = None
    if body.arv and body.renovation_budget is not None:
        reno = body.renovation_budget * (1 + body.contingency_pct)
        max_bid = max_purchase_price(body.arv, reno_max=reno, acq_rate_max=body.acquisition_rate,
            minimum_profit=body.desired_profit, target_roi=body.target_roi)
    verdict = "UNKNOWN"
    below_max = None
    if max_bid is not None:
        below_max = round(max_bid - body.my_offer, -2)
        verdict = "WITHIN_CRITERIA" if body.my_offer <= max_bid else "ABOVE_MAX_BID"
    expected_profit = expected_roi = None
    if body.arv and body.renovation_budget is not None:
        acq = body.my_offer * body.acquisition_rate
        cont = body.renovation_budget * body.contingency_pct
        total = body.my_offer + acq + body.renovation_budget + cont
        expected_profit = round(body.arv - total, -2)
        expected_roi = round(expected_profit / total * 100, 1) if total else None
    return {"asking_price": body.asking_price, "my_offer": body.my_offer,
            "discount_pct": round(discount, 1), "max_bid": max_bid,
            "offer_vs_max": below_max, "verdict": verdict,
            "expected_profit": expected_profit, "expected_roi_pct": expected_roi}

@router.get("/properties/{property_id}/due-diligence")
def get_dd(property_id: int, db: Session = Depends(get_db)):
    rows = db.query(DueDiligenceItem).filter(DueDiligenceItem.property_id == property_id).all()
    by_key = {r.item_key: r for r in rows}
    return [{"item_key": k, "status": by_key[k].status if k in by_key else "UNKNOWN",
             "notes": by_key[k].notes if k in by_key else None} for k in DD_ITEMS]

class DDUpdate(BaseModel):
    item_key: str
    status: str
    notes: Optional[str] = None

@router.put("/properties/{property_id}/due-diligence")
def update_dd(property_id: int, body: DDUpdate, db: Session = Depends(get_db)):
    if body.status not in ("UNKNOWN","PASS","WARNING","FAIL"):
        raise HTTPException(400, "Invalid status")
    if body.item_key not in DD_ITEMS:
        raise HTTPException(400, f"Unknown item")
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop: raise HTTPException(404, "Not found")
    row = db.query(DueDiligenceItem).filter(DueDiligenceItem.property_id==property_id, DueDiligenceItem.item_key==body.item_key).first()
    if not row:
        row = DueDiligenceItem(property_id=property_id, item_key=body.item_key)
        db.add(row)
    row.status = body.status
    row.notes = body.notes
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"item_key": body.item_key, "status": body.status}

@router.get("/properties/{property_id}/deal-quality")
def deal_quality(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop: raise HTTPException(404, "Not found")
    deal = analyze_deal(db, prop)
    conf_map = {"HIGH": 0.9, "MEDIUM": 0.55, "LOW": 0.25}
    conf = conf_map.get(deal.get("valuation_confidence") or "LOW", 0.25)
    deal_score = float(prop.investment_score or 5)
    risk = float(prop.risk_score or 5)
    risk_adj = max(0.3, 1 - (risk - 5) * 0.1)
    return {"deal_score": deal_score, "confidence_label": deal.get("valuation_confidence"),
            "confidence_pct": round(conf * 100), "risk_score": risk,
            "risk_adjusted_deal_score": round(deal_score * conf * risk_adj, 2),
            "comparable_count": deal.get("comparable_count"),
            "note": "High deal score with low confidence is not ranked as best deal."}

def comparable_quality(c):
    score = sum([bool(c.living_area), bool(c.postal_code), bool(c.property_type),
                 bool(c.condition), bool(c.epc_label), bool(c.observed_at)])
    if c.is_demo: return "LOW"
    if score >= 5: return "HIGH"
    if score >= 3: return "MEDIUM"
    return "LOW"

@router.get("/market-data")
def market_data(postal_code: Optional[str] = None, property_type: Optional[str] = None,
                min_area: Optional[float] = None, max_area: Optional[float] = None,
                source: Optional[str] = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(ComparableProperty)
    if postal_code: q = q.filter(ComparableProperty.postal_code == postal_code)
    if property_type: q = q.filter(ComparableProperty.property_type == property_type)
    if min_area: q = q.filter(ComparableProperty.living_area >= min_area)
    if max_area: q = q.filter(ComparableProperty.living_area <= max_area)
    if source: q = q.filter(ComparableProperty.source == source)
    rows = q.limit(limit).all()
    ppm2s = [c.price_per_m2 for c in rows if c.price_per_m2]
    outlier_info = detect_ppm2_outliers(ppm2s) if ppm2s else {}
    out = []
    for c in rows:
        is_out = False
        if c.price_per_m2 and ppm2s:
            try:
                is_out = ppm2s.index(c.price_per_m2) in outlier_info.get("outlier_indices", [])
            except ValueError: pass
        out.append({"id": c.id, "title": c.title, "postal_code": c.postal_code, "price": c.price,
            "living_area": c.living_area, "price_per_m2": c.price_per_m2, "condition": c.condition,
            "source": c.source, "is_demo": c.is_demo, "quality": comparable_quality(c),
            "possible_outlier": is_out,
            "observed_at": c.observed_at.isoformat() if c.observed_at else None})
    return {"comparables": out, "median_ppm2": outlier_info.get("median"),
            "trimmed_median_ppm2": outlier_info.get("trimmed_median"),
            "outlier_count": len(outlier_info.get("outlier_indices", [])),
            "note": "DEMO comparables are quality=LOW and must not be treated as market prices."}

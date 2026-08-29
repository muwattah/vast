"""Favorites status, property status, saved searches, notifications, history."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from backend.database.db import get_db
from backend.models.property import (
    Property, Favorite, PropertyStatus, PriceHistory,
    SavedSearch, Notification, AuditLog,
)

router = APIRouter()


class FavoriteUpdate(BaseModel):
    notes: Optional[str] = None
    favorite_status: Optional[str] = None


@router.get("/favorites")
def list_favorites(db: Session = Depends(get_db)):
    rows = db.query(Favorite).all()
    out = []
    for f in rows:
        p = f.property
        out.append({
            "id": f.id, "property_id": f.property_id, "notes": f.notes,
            "favorite_status": getattr(f, "favorite_status", "NEW") or "NEW",
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "title": p.title if p else None, "price": p.price if p else None,
            "postal_code": p.postal_code if p else None, "source": p.source if p else None,
        })
    return out


@router.post("/favorites/{property_id}")
def add_favorite(property_id: int, body: Optional[FavoriteUpdate] = None, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Property not found")
    existing = db.query(Favorite).filter(Favorite.property_id == property_id).first()
    if existing:
        if body:
            if body.notes is not None:
                existing.notes = body.notes
            if body.favorite_status is not None:
                existing.favorite_status = body.favorite_status
            db.commit()
        return {"status": "exists", "id": existing.id}
    fav = Favorite(
        property_id=property_id,
        notes=body.notes if body else None,
        favorite_status=(body.favorite_status if body and body.favorite_status else "NEW"),
    )
    db.add(fav)
    db.add(AuditLog(entity_type="favorite", entity_id=property_id, action="add", source="user"))
    db.commit()
    db.refresh(fav)
    return {"status": "created", "id": fav.id}


@router.patch("/favorites/{property_id}")
def update_favorite(property_id: int, body: FavoriteUpdate, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.property_id == property_id).first()
    if not fav:
        raise HTTPException(404, "Favorite not found")
    old = {"notes": fav.notes, "favorite_status": fav.favorite_status}
    if body.notes is not None:
        fav.notes = body.notes
    if body.favorite_status is not None:
        fav.favorite_status = body.favorite_status
    db.add(AuditLog(entity_type="favorite", entity_id=property_id, action="update",
                    old_value=old, new_value=body.model_dump(exclude_none=True), source="user"))
    db.commit()
    return {"status": "updated"}


@router.delete("/favorites/{property_id}")
def remove_favorite(property_id: int, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.property_id == property_id).first()
    if not fav:
        raise HTTPException(404, "Not found")
    db.delete(fav)
    db.commit()
    return {"status": "deleted"}


class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


@router.put("/properties/{property_id}/status")
def set_property_status(property_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Property not found")
    allowed = {"NEW", "WATCHING", "VISITED", "OFFER_SENT", "SOLD", "DISMISSED"}
    if body.status not in allowed:
        raise HTTPException(400, f"status must be one of {allowed}")
    row = db.query(PropertyStatus).filter(PropertyStatus.property_id == property_id).first()
    old = row.status if row else None
    if not row:
        row = PropertyStatus(property_id=property_id, status=body.status, notes=body.notes)
        db.add(row)
    else:
        row.status = body.status
        if body.notes is not None:
            row.notes = body.notes
        row.updated_at = datetime.utcnow()
    db.add(AuditLog(entity_type="property_status", entity_id=property_id, action="set",
                    old_value={"status": old}, new_value={"status": body.status}, source="user"))
    db.commit()
    return {"status": body.status}


@router.get("/properties/{property_id}/status")
def get_property_status(property_id: int, db: Session = Depends(get_db)):
    row = db.query(PropertyStatus).filter(PropertyStatus.property_id == property_id).first()
    if not row:
        return {"status": "NEW", "notes": None}
    return {"status": row.status, "notes": row.notes,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None}


@router.get("/properties/{property_id}/history")
def price_history(property_id: int, db: Session = Depends(get_db)):
    rows = db.query(PriceHistory).filter(PriceHistory.property_id == property_id).order_by(PriceHistory.recorded_at).all()
    return [{"price": r.price, "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
             "source": r.source} for r in rows]


@router.post("/properties/{property_id}/history")
def add_price_point(property_id: int, price: float, source: str = "manual", db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Not found")
    db.add(PriceHistory(property_id=property_id, price=price, source=source))
    db.commit()
    return {"status": "recorded"}


class SavedSearchIn(BaseModel):
    name: str
    filters: dict


@router.get("/saved-searches")
def list_searches(db: Session = Depends(get_db)):
    return [{"id": s.id, "name": s.name, "filters": s.filters, "is_active": s.is_active,
             "created_at": s.created_at.isoformat() if s.created_at else None}
            for s in db.query(SavedSearch).all()]


@router.post("/saved-searches")
def create_search(body: SavedSearchIn, db: Session = Depends(get_db)):
    s = SavedSearch(name=body.name, filters=body.filters)
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "name": s.name}


@router.delete("/saved-searches/{search_id}")
def delete_search(search_id: int, db: Session = Depends(get_db)):
    s = db.query(SavedSearch).filter(SavedSearch.id == search_id).first()
    if not s:
        raise HTTPException(404, "Not found")
    db.delete(s)
    db.commit()
    return {"status": "deleted"}


@router.get("/notifications")
def list_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Notification).order_by(Notification.created_at.desc())
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return [{"id": n.id, "title": n.title, "body": n.body, "property_id": n.property_id,
             "is_read": n.is_read, "created_at": n.created_at.isoformat() if n.created_at else None}
            for n in q.limit(50).all()]


@router.post("/notifications/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notif_id).first()
    if not n:
        raise HTTPException(404, "Not found")
    n.is_read = True
    db.commit()
    return {"status": "read"}


@router.post("/notifications/check")
def check_saved_searches(db: Session = Depends(get_db)):
    searches = db.query(SavedSearch).filter(SavedSearch.is_active == True).all()
    created = 0
    for s in searches:
        f = s.filters or {}
        q = db.query(Property).filter(Property.is_active == True)
        if f.get("max_price"):
            q = q.filter(Property.price <= f["max_price"])
        if f.get("min_price"):
            q = q.filter(Property.price >= f["min_price"])
        if f.get("postal_code"):
            q = q.filter(Property.postal_code == f["postal_code"])
        if f.get("min_diy"):
            q = q.filter(Property.diy_score >= f["min_diy"])
        if f.get("min_score"):
            q = q.filter(Property.investment_score >= f["min_score"])
        for p in q.limit(20).all():
            exists = db.query(Notification).filter(
                Notification.property_id == p.id, Notification.saved_search_id == s.id,
            ).first()
            if exists:
                continue
            db.add(Notification(
                title=f"Match: {s.name}",
                body=f"{p.title[:80]} — EUR {p.price:,.0f} — DIY {p.diy_score}",
                property_id=p.id, saved_search_id=s.id,
            ))
            created += 1
    db.commit()
    return {"notifications_created": created}


@router.get("/audit")
def list_audit(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [{"id": a.id, "entity_type": a.entity_type, "entity_id": a.entity_id,
             "action": a.action, "old_value": a.old_value, "new_value": a.new_value,
             "source": a.source, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in rows]

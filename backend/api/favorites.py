from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.models.property import Property, Favorite
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()


class FavoriteOut(BaseModel):
    id: int
    property_id: int
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/favorites", response_model=List[FavoriteOut])
def list_favorites(db: Session = Depends(get_db)):
    return db.query(Favorite).all()


@router.post("/favorites/{property_id}")
def add_favorite(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(404, "Property not found")
    existing = db.query(Favorite).filter(Favorite.property_id == property_id).first()
    if existing:
        return {"status": "already_exists", "id": existing.id}
    fav = Favorite(property_id=property_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"status": "added", "id": fav.id}


@router.delete("/favorites/{property_id}")
def remove_favorite(property_id: int, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.property_id == property_id).first()
    if not fav:
        raise HTTPException(404, "Favorite not found")
    db.delete(fav)
    db.commit()
    return {"status": "removed"}

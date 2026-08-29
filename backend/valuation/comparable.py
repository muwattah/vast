"""Comparable matching and similarity scoring."""
from typing import List, Tuple
from sqlalchemy.orm import Session
from backend.models.property import Property, ComparableProperty


def similarity_score(subject: Property, comp: ComparableProperty) -> float:
    score = 0.0
    weights_used = 0.0
    if subject.property_type and comp.property_type:
        weights_used += 20
        if subject.property_type.lower() == comp.property_type.lower():
            score += 20
    if subject.postal_code and comp.postal_code:
        weights_used += 25
        if subject.postal_code == comp.postal_code:
            score += 25
        elif subject.city and comp.city and subject.city == comp.city:
            score += 12
    elif subject.city and comp.city:
        weights_used += 15
        if subject.city == comp.city:
            score += 15
    if subject.living_area and comp.living_area and subject.living_area > 0:
        weights_used += 30
        ratio = min(subject.living_area, comp.living_area) / max(subject.living_area, comp.living_area)
        if ratio >= 0.85:
            score += 30
        elif ratio >= 0.70:
            score += 20
        elif ratio >= 0.55:
            score += 10
    if subject.bedrooms is not None and comp.bedrooms is not None:
        weights_used += 10
        diff = abs(subject.bedrooms - comp.bedrooms)
        if diff == 0:
            score += 10
        elif diff == 1:
            score += 5
    if subject.year_built and comp.year_built:
        weights_used += 10
        diff = abs(subject.year_built - comp.year_built)
        if diff <= 15:
            score += 10
        elif diff <= 40:
            score += 5
    if subject.epc_label and comp.epc_label:
        weights_used += 5
        if subject.epc_label == comp.epc_label:
            score += 5
    if weights_used == 0:
        return 0.0
    return round(min(100.0, (score / weights_used) * 100), 1)


def find_comparables(db: Session, subject: Property, min_similarity: float = 70.0, limit: int = 20):
    q = db.query(ComparableProperty)
    if subject.property_type:
        q = q.filter(ComparableProperty.property_type == subject.property_type)
    if subject.city:
        q = q.filter(ComparableProperty.city == subject.city)
    candidates = q.all()
    scored = []
    for c in candidates:
        s = similarity_score(subject, c)
        if s >= min_similarity:
            scored.append((c, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]

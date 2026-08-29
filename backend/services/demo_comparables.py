"""DEMO comparables — clearly marked. Not real observed sales."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models.property import ComparableProperty

DEMO_COMPARABLES = [
    {"title": "[DEMO] Gerenoveerd huis – omgeving Park Spoor Noord", "postal_code": "2060", "city": "Antwerpen",
     "district": "Antwerpen-Noord", "property_type": "huis", "living_area": 75, "bedrooms": 2,
     "year_built": 1890, "epc_label": "C", "condition": "renovated", "price": 285000, "is_demo": True},
    {"title": "[DEMO] Opgeknapte arbeiderswoning – 2060", "postal_code": "2060", "city": "Antwerpen",
     "property_type": "huis", "living_area": 70, "bedrooms": 1, "year_built": 1900, "epc_label": "D",
     "condition": "renovated", "price": 265000, "is_demo": True},
    {"title": "[DEMO] Te renoveren huis – 2060 (comp)", "postal_code": "2060", "city": "Antwerpen",
     "property_type": "huis", "living_area": 72, "bedrooms": 2, "year_built": 1880, "epc_label": "E",
     "condition": "to_renovate", "price": 175000, "is_demo": True},
    {"title": "[DEMO] Gerenoveerd rijhuis – Slachthuiswijk", "postal_code": "2060", "city": "Antwerpen",
     "property_type": "huis", "living_area": 145, "bedrooms": 4, "year_built": 1925, "epc_label": "C",
     "condition": "renovated", "price": 420000, "is_demo": True},
    {"title": "[DEMO] Deels gerenoveerd – 2060 groot", "postal_code": "2060", "city": "Antwerpen",
     "property_type": "huis", "living_area": 130, "bedrooms": 5, "year_built": 1915, "epc_label": "D",
     "condition": "partial", "price": 310000, "is_demo": True},
    {"title": "[DEMO] Gerenoveerd huis – Zurenborg", "postal_code": "2018", "city": "Antwerpen",
     "district": "Zurenborg", "property_type": "huis", "living_area": 170, "bedrooms": 4,
     "year_built": 1910, "epc_label": "B", "condition": "renovated", "price": 595000, "is_demo": True},
    {"title": "[DEMO] Instapklaar – Dageraadplaats omgeving", "postal_code": "2018", "city": "Antwerpen",
     "property_type": "huis", "living_area": 160, "bedrooms": 3, "year_built": 1905, "epc_label": "C",
     "condition": "turnkey", "price": 550000, "is_demo": True},
    {"title": "[DEMO] Te renoveren – Zurenborg rand", "postal_code": "2018", "city": "Antwerpen",
     "property_type": "huis", "living_area": 175, "bedrooms": 4, "year_built": 1912, "epc_label": "F",
     "condition": "to_renovate", "price": 340000, "is_demo": True},
    {"title": "[DEMO] Gerenoveerd – Borgerhout / Zurenborg-grens", "postal_code": "2140", "city": "Antwerpen",
     "property_type": "huis", "living_area": 190, "bedrooms": 5, "year_built": 1910, "epc_label": "C",
     "condition": "renovated", "price": 475000, "is_demo": True},
    {"title": "[DEMO] Gerenoveerd rijhuis – 2140", "postal_code": "2140", "city": "Antwerpen",
     "property_type": "huis", "living_area": 180, "bedrooms": 4, "year_built": 1920, "epc_label": "D",
     "condition": "renovated", "price": 440000, "is_demo": True},
    {"title": "[DEMO] Gerenoveerd huis – Ekeren", "postal_code": "2180", "city": "Antwerpen",
     "property_type": "huis", "living_area": 125, "bedrooms": 3, "year_built": 1960, "epc_label": "C",
     "condition": "renovated", "price": 355000, "is_demo": True},
    {"title": "[DEMO] Te renoveren – Ekeren (comp)", "postal_code": "2180", "city": "Antwerpen",
     "property_type": "huis", "living_area": 115, "bedrooms": 3, "year_built": 1950, "epc_label": "F",
     "condition": "to_renovate", "price": 195000, "is_demo": True},
]


def seed_demo_comparables(db: Session):
    count = db.query(ComparableProperty).filter(ComparableProperty.is_demo == True).count()
    if count > 0:
        return count
    for item in DEMO_COMPARABLES:
        c = ComparableProperty(
            source="demo", title=item["title"], postal_code=item.get("postal_code"),
            city=item.get("city", "Antwerpen"), district=item.get("district"),
            property_type=item.get("property_type"), living_area=item.get("living_area"),
            bedrooms=item.get("bedrooms"), year_built=item.get("year_built"),
            epc_label=item.get("epc_label"), condition=item.get("condition"),
            price=item["price"], url="https://example.com/demo-comp",
            observed_at=datetime.utcnow() - timedelta(days=30), is_demo=True,
            notes="DEMO comparable – not a real transaction",
        )
        c.compute_ppm2()
        db.add(c)
    db.commit()
    return len(DEMO_COMPARABLES)

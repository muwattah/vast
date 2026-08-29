"""Core unit tests for Antwerp Property Investor."""
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.database.db import Base, engine, SessionLocal
from backend.models.property import Property
from backend.importers.base_importer import make_content_hash, detect_renovation_flags, normalize_epc
from backend.importers.json_importer import JsonImporter
from backend.importers.csv_importer import CsvImporter
from backend.importers.service import upsert_properties
from backend.ai.analyzer import rule_based_analysis, analyze_property, apply_analysis
from backend.ai.schemas import AnalysisResult


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_content_hash_stable():
    d = {"price": 200000, "living_area": 100, "epc_label": "E", "description": "test", "title": "Huis"}
    h1 = make_content_hash(d)
    h2 = make_content_hash(d)
    assert h1 == h2
    d["price"] = 210000
    assert make_content_hash(d) != h1


def test_detect_renovation():
    f = detect_renovation_flags("Totaal te renoveren woning met EPC F")
    assert f["is_to_renovate"] is True
    assert f["is_fully_to_renovate"] is True


def test_normalize_epc():
    assert normalize_epc("EPC F") == "F"
    assert normalize_epc("label B") == "B"
    assert normalize_epc(None) is None


def test_price_per_m2():
    p = Property(title="t", url="u", source="demo", price=200000, living_area=100)
    assert p.price_per_m2() == 2000.0
    p2 = Property(title="t", url="u", source="demo", price=None, living_area=100)
    assert p2.price_per_m2() is None


def test_rule_based_scoring():
    p = Property(
        title="Te renoveren huis Antwerpen", url="http://x", source="demo",
        price=165000, living_area=68, postal_code="2060", epc_label="E",
        is_to_renovate=True, is_fully_to_renovate=True,
    )
    a = rule_based_analysis(p)
    assert 1 <= a["diy_score"] <= 10
    assert 1 <= a["investment_score"] <= 10
    assert a["estimated_renovation_cost_min"] < a["estimated_renovation_cost_max"]
    assert a["estimated_acquisition_cost_min"] > 0
    assert a["estimated_total_investment_min"] >= p.price
    assert "uncertainty_notes" in a


def test_roi_and_margin_ranges():
    p = Property(
        title="x", url="u", source="demo", price=250000, living_area=120,
        postal_code="2018", epc_label="F", is_fully_to_renovate=True,
    )
    a = rule_based_analysis(p)
    assert a["estimated_profit_min"] <= a["estimated_profit_max"]
    assert a["roi_min"] <= a["roi_max"]


def test_json_import():
    payload = json.dumps([{
        "title": "Import test huis", "price": 220000, "living_area": 110,
        "postal_code": "2140", "epc_label": "E",
        "description": "Te renoveren woning in Borgerhout",
    }])
    items = JsonImporter().parse(payload)
    assert len(items) == 1
    assert items[0]["source"] == "import"
    assert items[0]["is_to_renovate"] is True
    assert items[0]["price"] == 220000


def test_csv_import():
    csv_data = "title,price,living_area,postal_code,epc_label,description\nTest CSV,180000,90,2060,F,te renoveren\n"
    items = CsvImporter().parse(csv_data)
    assert len(items) == 1
    assert items[0]["price"] == 180000
    assert items[0]["epc_label"] == "F"


def test_upsert_and_duplicate():
    db = SessionLocal()
    items = JsonImporter().parse(json.dumps([{
        "title": "Dup test", "price": 100000, "living_area": 50,
        "postal_code": "2000", "source_listing_id": "dup-1",
    }]))
    s1 = upsert_properties(db, items, run_analysis=True)
    assert s1["created"] == 1
    s2 = upsert_properties(db, items, run_analysis=True)
    assert s2["skipped"] == 1
    items[0]["price"] = 105000
    items[0]["content_hash"] = make_content_hash(items[0])
    s3 = upsert_properties(db, items, run_analysis=True)
    assert s3["updated"] == 1
    db.close()


def test_analysis_result_schema():
    data = {
        "diy_score": 8, "renovation_score": 7, "price_score": 8,
        "margin_score": 6, "location_score": 7, "risk_score": 5,
        "investment_score": 7.2,
        "estimated_renovation_cost_min": 50000, "estimated_renovation_cost_max": 80000,
        "estimated_after_renovation_value_min": 300000, "estimated_after_renovation_value_max": 350000,
        "estimated_profit_min": 10000, "estimated_profit_max": 50000,
        "roi_min": 3, "roi_max": 15, "renovation_level": "medium",
        "diy_tasks": ["paint"], "professional_tasks": ["electric"],
        "opportunities": ["loc"], "risks": ["roof"], "summary": "ok",
    }
    r = AnalysisResult.model_validate(data)
    assert r.diy_score == 8


def test_apply_analysis_writes_fields():
    db = SessionLocal()
    p = Property(title="apply test", url="u", source="demo", price=150000, living_area=80, postal_code="2060", epc_label="E", is_to_renovate=True)
    a = analyze_property(p)
    apply_analysis(p, a)
    assert p.investment_score is not None
    assert p.estimated_acquisition_cost_min is not None
    assert p.ai_model is not None
    assert p.ai_analyzed_at is not None
    db.add(p)
    db.commit()
    db.close()


if __name__ == "__main__":
    setup_module()
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("ALL TESTS PASSED")

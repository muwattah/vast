"""Tests for phases 4-8: tools, investor features, quality."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.database.db import Base, engine, SessionLocal
from backend.models.property import (
    Property, Favorite, PropertyStatus, PriceHistory,
    SavedSearch, Notification, AuditLog,
)
from backend.valuation.deal_analyzer import max_purchase_price
from backend.api.tools import completeness_score, risk_flags
from backend.ai.analyzer import rule_based_analysis, apply_analysis
from backend.services.demo_comparables import DEMO_COMPARABLES


def setup():
    Base.metadata.create_all(bind=engine)


def make_prop(**kw):
    d = dict(title="T", url="u", source="demo", price=200000, living_area=100,
             postal_code="2060", city="Antwerpen", property_type="huis",
             epc_label="E", is_to_renovate=True)
    d.update(kw)
    p = Property(**d)
    apply_analysis(p, rule_based_analysis(p))
    return p


def test_max_bid_endpoint_logic():
    mp = max_purchase_price(400000, 80000, minimum_profit=50000, target_roi=0.2)
    assert mp is not None and mp < 400000


def test_completeness_full():
    p = make_prop(description="x"*60, bedrooms=2, year_built=1900, address="straat", images=["a"])
    assert completeness_score(p) >= 80


def test_completeness_sparse():
    p = Property(title="t", url="u", source="demo")
    assert completeness_score(p) < 50


def test_risk_flags_epc():
    p = make_prop(epc_label="F", is_fully_to_renovate=True)
    flags = risk_flags(p)
    assert any("EPC" in f for f in flags)


def test_risk_flags_always_include_unknowns():
    p = make_prop()
    flags = risk_flags(p)
    assert any("electrical" in f.lower() for f in flags)
    assert any("asbestos" in f.lower() for f in flags)


def test_favorite_status_cycle():
    setup()
    db = SessionLocal()
    p = make_prop()
    db.add(p)
    db.commit()
    fav = Favorite(property_id=p.id, favorite_status="RESEARCHING", notes="check dak")
    db.add(fav)
    db.commit()
    assert db.query(Favorite).first().favorite_status == "RESEARCHING"
    db.close()


def test_property_status():
    setup()
    db = SessionLocal()
    p = make_prop()
    db.add(p)
    db.commit()
    db.add(PropertyStatus(property_id=p.id, status="VISITED", notes="ok"))
    db.commit()
    assert db.query(PropertyStatus).filter(PropertyStatus.status == "VISITED").count() == 1
    db.close()


def test_price_history():
    setup()
    db = SessionLocal()
    p = make_prop(price=300000)
    db.add(p)
    db.commit()
    db.add(PriceHistory(property_id=p.id, price=300000, source="import"))
    db.add(PriceHistory(property_id=p.id, price=285000, source="import"))
    db.commit()
    hist = db.query(PriceHistory).filter(PriceHistory.property_id == p.id).all()
    assert len(hist) == 2
    db.close()


def test_saved_search():
    setup()
    db = SessionLocal()
    db.add(SavedSearch(name="Antwerp DIY", filters={"max_price": 300000, "min_diy": 8}))
    db.commit()
    assert db.query(SavedSearch).count() == 1
    db.close()


def test_notification_create():
    setup()
    db = SessionLocal()
    db.add(Notification(title="New deal", body="test", is_read=False))
    db.commit()
    assert db.query(Notification).filter(Notification.is_read == False).count() >= 1
    db.close()


def test_audit_log():
    setup()
    db = SessionLocal()
    db.add(AuditLog(entity_type="favorite", entity_id=1, action="add", source="user"))
    db.commit()
    assert db.query(AuditLog).count() >= 1
    db.close()


def test_scenario_math():
    purchase, reno, acq_rate, cont_pct, arv = 250000, 70000, 0.10, 0.10, 400000
    total = purchase + purchase * acq_rate + reno + reno * cont_pct
    profit = arv - total
    assert total == 352000
    assert profit == 48000


def test_demo_comps_not_market_claim():
    assert all("[DEMO]" in c["title"] or c.get("is_demo") for c in DEMO_COMPARABLES)


def test_max_bid_respects_minimum_profit():
    mp_low = max_purchase_price(300000, 50000, minimum_profit=100000, target_roi=0.05)
    mp_high = max_purchase_price(300000, 50000, minimum_profit=10000, target_roi=0.05)
    if mp_low and mp_high:
        assert mp_low <= mp_high


def test_init_creates_all_tables():
    setup()
    from sqlalchemy import inspect
    tables = inspect(engine).get_table_names()
    for t in ["properties", "comparables", "favorites", "property_statuses",
              "price_history", "saved_searches", "notifications", "audit_logs"]:
        assert t in tables, f"missing {t}"


if __name__ == "__main__":
    setup()
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as e:
                print(f"FAIL {name}: {e}")
                fails += 1
    print("DONE fails=", fails)
    raise SystemExit(1 if fails else 0)

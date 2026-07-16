"""Phase F1 — tax KPI aggregation and CSV export tests."""

from datetime import datetime, timezone, timedelta
import uuid

import pytest

from apps.reports.tax_kpis import aggregate_tax_kpis, export_tax_assessments_csv_rows
from apps.reports.services import ReportsService


def _insert_assessment(test_db, **kwargs):
    doc = {
        "assessment_id": str(uuid.uuid4()),
        "trader_id": kwargs.get("trader_id", str(uuid.uuid4())),
        "business_id": str(uuid.uuid4()),
        "tax_category": "BOP",
        "period_label": kwargs.get("period_label", "2026"),
        "business_type": kwargs.get("business_type", "food_vendor"),
        "region": kwargs.get("region", "Greater Accra"),
        "district": kwargs.get("district", "Accra Metro"),
        "amount_due": kwargs.get("amount_due", 10000),  # 100 GHS
        "amount_paid": kwargs.get("amount_paid", 0),
        "status": kwargs.get("status", "PENDING"),
        "due_date": kwargs.get("due_date", datetime.now(timezone.utc) + timedelta(days=30)),
        "created_at": datetime.now(timezone.utc),
    }
    test_db["tax_assessments"].insert_one(doc)
    return doc


@pytest.mark.django_db
def test_tax_kpi_math_hand_calculated(test_db):
    # 100 + 50 = 150 GHS assessed; 40 + 0 = 40 GHS collected → 40/150 = 26.666...%
    _insert_assessment(test_db, amount_due=10000, amount_paid=4000, business_type="food_vendor")
    _insert_assessment(test_db, amount_due=5000, amount_paid=0, business_type="clothing")

    kpis = aggregate_tax_kpis()
    assert kpis["_total_assessed_pesewas"] == 15000
    assert kpis["_total_collected_pesewas"] == 4000
    assert kpis["total_assessed_ghs"] == 150.0
    assert kpis["total_collected_ghs"] == 40.0
    assert kpis["collection_rate_pct"] == pytest.approx(26.67, abs=0.01)
    assert kpis["assessment_count"] == 2


@pytest.mark.django_db
def test_tax_kpi_zero_assessed_rate_is_zero(test_db):
    kpis = aggregate_tax_kpis()
    assert kpis["total_assessed_ghs"] == 0.0
    assert kpis["collection_rate_pct"] == 0.0


@pytest.mark.django_db
def test_overdue_count_query_time(test_db):
    past = datetime.now(timezone.utc) - timedelta(days=5)
    future = datetime.now(timezone.utc) + timedelta(days=10)
    # overdue PENDING
    _insert_assessment(test_db, status="PENDING", due_date=past, amount_due=1000)
    # overdue PARTIAL
    _insert_assessment(test_db, status="PARTIAL", due_date=past, amount_due=2000, amount_paid=500)
    # not due yet
    _insert_assessment(test_db, status="PENDING", due_date=future, amount_due=3000)
    # paid past due — should NOT count
    _insert_assessment(test_db, status="PAID", due_date=past, amount_due=4000, amount_paid=4000)

    kpis = aggregate_tax_kpis()
    assert kpis["overdue_count"] == 2


@pytest.mark.django_db
def test_tax_csv_export_columns(test_db):
    tid = str(uuid.uuid4())
    test_db["traders"].insert_one({
        "trader_id": tid,
        "name": "Ama Trader",
        "phone_number": "+233200000099",
        "business_type": "food_vendor",
        "region": "Ashanti",
        "district": "Kumasi",
        "market_name": "Kejetia",
        "tin_number": "GH-TIN-TEST01",
        "created_at": datetime.now(timezone.utc),
    })
    _insert_assessment(
        test_db,
        trader_id=tid,
        amount_due=2500,
        amount_paid=1000,
        period_label="2026",
        business_type="food_vendor",
        region="Ashanti",
        district="Kumasi",
    )
    rows = export_tax_assessments_csv_rows({"period_label": "2026"})
    assert len(rows) == 1
    assert rows[0]["trader_name"] == "Ama Trader"
    for col in (
        "assessment_id", "trader_name", "business_name", "business_type",
        "tax_category", "period_label", "amount_due", "amount_paid",
        "status", "due_date", "region", "district",
    ):
        assert col in rows[0]


@pytest.mark.django_db
def test_summary_includes_tax_block(tax_admin_doc, test_db):
    _insert_assessment(test_db, amount_due=10000, amount_paid=2500)
    svc = ReportsService()
    result = svc.get_summary(
        period="all",
        actor=tax_admin_doc,
        tax_filters={},
    )
    assert "tax" in result
    assert result["tax"]["total_assessed_ghs"] == 100.0
    assert result["tax"]["total_collected_ghs"] == 25.0
    assert result["tax"]["collection_rate_pct"] == 25.0


@pytest.mark.django_db
def test_export_tax_type_endpoint(auth_client_tax, test_db):
    _insert_assessment(test_db, amount_due=1000)
    resp = auth_client_tax.get("/api/reports/export/?type=tax")
    assert resp.status_code == 200
    assert "text/csv" in resp["Content-Type"]
    body = resp.content.decode()
    assert "assessment_id" in body.splitlines()[0]

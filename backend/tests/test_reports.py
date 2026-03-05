"""
test_reports.py — ReportsService and reports endpoint tests.

Covers:
- Summary returns correct totals
- Summary by channel correct
- Export CSV has correct columns
- Performance under 3s for 10k records (skipped in CI without real Mongo)
"""

import csv
import io
import time
import uuid
from datetime import datetime, timezone, timedelta

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _insert_traders(db, count: int, channel: str = "web", business_type: str = "retail"):
    """Insert `count` trader docs with controllable fields."""
    now = datetime.now(timezone.utc)
    docs = []
    for i in range(count):
        docs.append({
            "trader_id": str(uuid.uuid4()),
            "tin_number": f"GH-TIN-{uuid.uuid4().hex[:6].upper()}",
            "name": f"Trader {i}",
            "phone_number": f"+23320{i:07d}",
            "business_type": business_type,
            "region": "Greater Accra" if i % 2 == 0 else "Ashanti",
            "district": "Test District",
            "market_name": "Test Market",
            "channel": channel,
            "status": "active",
            "created_at": now - timedelta(days=i % 30),
            "updated_at": now,
        })
    if docs:
        db["traders"].insert_many(docs)


# ── Service-level tests ───────────────────────────────────────────────────────

class TestReportsService:
    def test_summary_returns_correct_total(self, test_db):
        _insert_traders(test_db, 10, channel="web")
        _insert_traders(test_db, 5, channel="ussd")

        from apps.reports.services import ReportsService
        svc = ReportsService()
        result = svc.get_summary("30d", actor={"admin_id": "test", "role": "SYS_ADMIN"})

        assert result["total_traders"] == 15
        assert "generated_at" in result

    def test_summary_by_channel_correct(self, test_db):
        _insert_traders(test_db, 8, channel="web")
        _insert_traders(test_db, 3, channel="ussd")

        from apps.reports.services import ReportsService
        svc = ReportsService()
        result = svc.get_summary("30d", actor={"admin_id": "test", "role": "SYS_ADMIN"})

        by_channel = result["by_channel"]
        assert by_channel.get("web", 0) == 8
        assert by_channel.get("ussd", 0) == 3

    def test_summary_by_business_type(self, test_db):
        _insert_traders(test_db, 4, business_type="food_vendor")
        _insert_traders(test_db, 6, business_type="clothing")

        from apps.reports.services import ReportsService
        svc = ReportsService()
        result = svc.get_summary("all", actor={"admin_id": "test", "role": "SYS_ADMIN"})

        types = {item["type"]: item["count"] for item in result["by_business_type"]}
        assert types.get("food_vendor") == 4
        assert types.get("clothing") == 6

    def test_get_traders_list_pagination(self, test_db):
        _insert_traders(test_db, 25)

        from apps.reports.services import ReportsService
        svc = ReportsService()
        result = svc.get_traders_list({"page": 1, "page_size": 10})

        assert result["total"] == 25
        assert len(result["traders"]) == 10
        assert result["total_pages"] == 3

    def test_get_traders_list_channel_filter(self, test_db):
        _insert_traders(test_db, 7, channel="web")
        _insert_traders(test_db, 3, channel="ussd")

        from apps.reports.services import ReportsService
        svc = ReportsService()
        result = svc.get_traders_list({"channel": "ussd", "page": 1, "page_size": 20})

        assert result["total"] == 3
        assert all(t["channel"] == "ussd" for t in result["traders"])

    def test_get_trader_detail_returns_business(self, test_db, sample_trader):
        from apps.reports.services import ReportsService
        svc = ReportsService()
        result = svc.get_trader_detail(sample_trader["trader_id"])

        assert result is not None
        assert result["tin_number"] == sample_trader["tin_number"]
        assert "business" in result

    def test_get_trader_detail_not_found_returns_none(self):
        from apps.reports.services import ReportsService
        svc = ReportsService()
        assert svc.get_trader_detail(str(uuid.uuid4())) is None


# ── Export CSV tests ──────────────────────────────────────────────────────────

class TestCSVExport:
    def test_export_csv_returns_correct_columns(self, test_db):
        _insert_traders(test_db, 3)

        from apps.reports.services import ReportsService, CSV_COLUMNS
        svc = ReportsService()
        csv_str = svc.export_csv(
            validated_params={},
            actor={"admin_id": "test", "role": "SYS_ADMIN"},
            ip_address="127.0.0.1",
        )

        reader = csv.DictReader(io.StringIO(csv_str))
        expected_headers = [col[0] for col in CSV_COLUMNS]
        assert list(reader.fieldnames) == expected_headers

    def test_export_csv_row_count(self, test_db):
        _insert_traders(test_db, 5)

        from apps.reports.services import ReportsService
        svc = ReportsService()
        csv_str = svc.export_csv(
            validated_params={},
            actor={"admin_id": "test", "role": "SYS_ADMIN"},
            ip_address="127.0.0.1",
        )

        rows = list(csv.DictReader(io.StringIO(csv_str)))
        assert len(rows) == 5

    def test_export_csv_writes_audit_log(self, test_db):
        from apps.reports.services import ReportsService
        svc = ReportsService()
        svc.export_csv(
            validated_params={},
            actor={"admin_id": "test_actor", "role": "TAX_ADMIN"},
            ip_address="10.0.0.1",
        )
        assert test_db["audit_logs"].count_documents({"action": "EXPORT_REPORT"}) == 1

    def test_export_csv_channel_filter(self, test_db):
        _insert_traders(test_db, 4, channel="web")
        _insert_traders(test_db, 2, channel="ussd")

        from apps.reports.services import ReportsService
        svc = ReportsService()
        csv_str = svc.export_csv(
            validated_params={"channel": "ussd"},
            actor={"admin_id": "test", "role": "SYS_ADMIN"},
            ip_address="127.0.0.1",
        )

        rows = list(csv.DictReader(io.StringIO(csv_str)))
        assert len(rows) == 2
        assert all(r["Channel"] == "ussd" for r in rows)


# ── Endpoint tests ────────────────────────────────────────────────────────────

class TestReportsEndpoints:
    def test_summary_endpoint_requires_auth(self, client):
        resp = client.get("/api/reports/summary")
        assert resp.status_code in (401, 403)

    def test_summary_endpoint_tax_admin_allowed(self, client, tax_admin_token, test_db):
        _insert_traders(test_db, 3)
        resp = client.get(
            "/api/reports/summary",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total_traders"] == 3

    def test_summary_period_param_7d(self, client, sys_admin_token, test_db):
        _insert_traders(test_db, 2)
        resp = client.get(
            "/api/reports/summary?period=7d",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["period"] == "7d"

    def test_summary_invalid_period_returns_400(self, client, sys_admin_token):
        resp = client.get(
            "/api/reports/summary?period=invalid",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 400

    def test_traders_list_endpoint(self, client, tax_admin_token, test_db):
        _insert_traders(test_db, 5)
        resp = client.get(
            "/api/traders/",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 5

    def test_trader_detail_endpoint(self, client, tax_admin_token, sample_trader):
        resp = client.get(
            f"/api/traders/{sample_trader['trader_id']}",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["tin_number"] == sample_trader["tin_number"]

    def test_trader_detail_not_found(self, client, sys_admin_token):
        resp = client.get(
            f"/api/traders/{uuid.uuid4()}",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 404

    def test_export_endpoint_returns_csv(self, client, tax_admin_token, test_db):
        _insert_traders(test_db, 2)
        resp = client.get(
            "/api/reports/export",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.get("Content-Type", "")
        assert "attachment" in resp.get("Content-Disposition", "")


# ── Performance test (skipped unless RUN_PERF_TESTS=1) ───────────────────────

@pytest.mark.skipif(
    not __import__("os").environ.get("RUN_PERF_TESTS"),
    reason="Performance test requires RUN_PERF_TESTS=1 and a live MongoDB instance",
)
class TestReportsPerformance:
    def test_summary_performance_under_3s(self, test_db):
        """Summary aggregation over 10k records must complete in ≤3 seconds."""
        _insert_traders(test_db, 10_000)

        from apps.reports.services import ReportsService
        svc = ReportsService()
        start = time.monotonic()
        svc.get_summary("all", actor={"admin_id": "perf", "role": "SYS_ADMIN"})
        elapsed = time.monotonic() - start

        assert elapsed < 3.0, f"Summary took {elapsed:.2f}s — expected < 3s"

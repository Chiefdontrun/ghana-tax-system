import pytest
from datetime import datetime, timezone
import uuid

from apps.tax.repository import TaxRateScheduleRepository, TaxAssessmentExceptionRepository
from core.utils.mongo import TAX_RATE_SCHEDULES, TAX_ASSESSMENTS, TAX_ASSESSMENT_EXCEPTIONS

@pytest.fixture
def base_schedule_payload():
    return {
        "tax_category": "BOP",
        "business_type": "food_vendor",
        "region": "Greater Accra",
        "district": "Osu",
        "rate_type": "FIXED",
        "fixed_amount": 5000,
        "effective_year": 2026,
        "is_active": True
    }


def test_create_schedule_success_fixed(auth_client_sys, base_schedule_payload, test_db):
    res = auth_client_sys.post("/api/tax/rate-schedules/", base_schedule_payload, content_type="application/json")
    assert res.status_code == 201
    assert res.json()["data"]["fixed_amount"] == 5000

    logs = list(test_db["audit_logs"].find({"action": "TAX_SCHEDULE_CREATED"}))
    assert len(logs) == 1


def test_create_schedule_fails_permission(auth_client_tax, base_schedule_payload):
    res = auth_client_tax.post("/api/tax/rate-schedules/", base_schedule_payload, content_type="application/json")
    assert res.status_code == 403


def test_create_schedule_validation_fixed_with_percentage(auth_client_sys, base_schedule_payload):
    payload = {**base_schedule_payload, "percentage_rate": 5}
    res = auth_client_sys.post("/api/tax/rate-schedules/", payload, content_type="application/json")
    assert res.status_code == 400
    assert "must not specify percentage_rate" in res.json()["message"]


def test_create_schedule_validation_percentage_without_rate(auth_client_sys, base_schedule_payload):
    payload = {**base_schedule_payload, "rate_type": "PERCENTAGE_TURNOVER"}
    payload.pop("fixed_amount")
    # missing percentage_rate
    res = auth_client_sys.post("/api/tax/rate-schedules/", payload, content_type="application/json")
    assert res.status_code == 400
    assert "require a percentage_rate" in res.json()["message"]


def test_update_schedule_deactivate_succeeds(auth_client_sys, base_schedule_payload, test_db):
    repo = TaxRateScheduleRepository()
    schedule_id = str(uuid.uuid4())
    doc = {**base_schedule_payload, "schedule_id": schedule_id, "created_at": datetime.now(timezone.utc)}
    repo._col().insert_one(doc)

    res = auth_client_sys.patch(f"/api/tax/rate-schedules/{schedule_id}/", {"is_active": False}, content_type="application/json")
    assert res.status_code == 200
    assert res.json()["data"]["is_active"] is False

    logs = list(test_db["audit_logs"].find({"action": "TAX_SCHEDULE_UPDATED"}))
    assert len(logs) == 1


def test_generate_batch_endpoint_and_exception_persistence(auth_client_sys, sample_trader, test_db):
    # Setup: we have a trader, but NO rate schedule for them
    # Therefore, generate_annual_assessments_batch will raise RateScheduleNotFoundError
    # and log an exception
    res = auth_client_sys.post("/api/tax/assessments/generate-batch/", {"year": 2026}, content_type="application/json")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["created"] == 0
    assert len(data["missing_schedule"]) == 1

    # Verify exception is in DB
    exceptions = list(test_db[TAX_ASSESSMENT_EXCEPTIONS].find())
    assert len(exceptions) == 1
    assert exceptions[0]["exception_type"] == "MISSING_SCHEDULE"
    assert exceptions[0]["status"] == "OPEN"

    # Verify batch audit log
    logs = list(test_db["audit_logs"].find({"action": "ASSESSMENT_GENERATED"}))
    assert len(logs) == 1
    assert logs[0]["entity_type"] == "batch"

    # Run again, check idempotency
    auth_client_sys.post("/api/tax/assessments/generate-batch/", {"year": 2026}, content_type="application/json")
    exceptions_after = list(test_db[TAX_ASSESSMENT_EXCEPTIONS].find())
    assert len(exceptions_after) == 1  # Did not duplicate


def test_resolve_turnover_exception(auth_client_tax, sample_trader, test_db):
    # Setup exception
    biz = test_db["businesses"].find_one({"owner_trader_id": sample_trader["trader_id"]})
    
    # Also we need a rate schedule so generate_assessment works after turnover is resolved
    repo = TaxRateScheduleRepository()
    repo._col().insert_one({
        "schedule_id": "s1", "tax_category": "BOP", "business_type": "food_vendor",
        "region": None, "district": None, "rate_type": "PERCENTAGE_TURNOVER", "percentage_rate": 10,
        "effective_year": 2026, "is_active": True
    })

    exc_repo = TaxAssessmentExceptionRepository()
    exc = exc_repo.create({
        "exception_id": "exc-1",
        "business_id": biz["business_id"],
        "trader_id": sample_trader["trader_id"],
        "tax_category": "BOP",
        "period_label": "2026",
        "exception_type": "NEEDS_TURNOVER",
        "status": "OPEN",
    })

    res = auth_client_tax.post(f"/api/tax/assessment-exceptions/exc-1/resolve-turnover/", {"declared_turnover_pesewas": 1000}, content_type="application/json")
    
    assert res.status_code == 200
    assert res.json()["data"]["assessment"]["amount_due"] == 100 # 10% of 1000

    updated_exc = exc_repo.find_by_id("exc-1")
    assert updated_exc["status"] == "RESOLVED"
    assert updated_exc["resolved_by"] is not None


def test_retry_missing_schedule_fails_if_still_missing(auth_client_tax, sample_trader, test_db):
    biz = test_db["businesses"].find_one({"owner_trader_id": sample_trader["trader_id"]})
    exc_repo = TaxAssessmentExceptionRepository()
    exc_repo.create({
        "exception_id": "exc-2",
        "business_id": biz["business_id"],
        "trader_id": sample_trader["trader_id"],
        "tax_category": "BOP",
        "period_label": "2026",
        "exception_type": "MISSING_SCHEDULE",
        "status": "OPEN",
    })

    res = auth_client_tax.post(f"/api/tax/assessment-exceptions/exc-2/retry/")
    assert res.status_code == 400
    assert "Schedule still missing" in res.json()["message"]

    updated_exc = exc_repo.find_by_id("exc-2")
    assert updated_exc["status"] == "OPEN"

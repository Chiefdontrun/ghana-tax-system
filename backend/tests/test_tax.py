import uuid
from datetime import datetime, timezone

from apps.tax.repository import (
    TaxAssessmentRepository,
    TaxPaymentRepository,
    TaxRateScheduleRepository,
)


def test_tax_rate_schedule_repository_create_and_find_by_id(test_db):
    repo = TaxRateScheduleRepository()
    schedule_id = str(uuid.uuid4())
    doc = {
        "schedule_id": schedule_id,
        "tax_category": "BOP",
        "business_type": "food_vendor",
        "region": None,
        "district": None,
        "rate_type": "FIXED",
        "fixed_amount": 120000,
        "percentage_rate": None,
        "min_amount": None,
        "max_amount": None,
        "period": "ANNUAL",
        "effective_year": 2026,
        "is_active": True,
        "created_by": "admin-1",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    created = repo.create(doc)
    fetched = repo.find_by_id(schedule_id)

    assert created["schedule_id"] == schedule_id
    assert fetched is not None
    assert fetched["tax_category"] == "BOP"
    assert fetched["fixed_amount"] == 120000


def test_tax_assessment_and_payment_repository_linkage(test_db):
    assessment_repo = TaxAssessmentRepository()
    payment_repo = TaxPaymentRepository()

    assessment_id = str(uuid.uuid4())
    assessment = {
        "assessment_id": assessment_id,
        "business_id": str(uuid.uuid4()),
        "trader_id": str(uuid.uuid4()),
        "tax_category": "BOP",
        "schedule_id": str(uuid.uuid4()),
        "period_label": "2026",
        "declared_turnover": None,
        "amount_due": 120000,
        "amount_paid": 0,
        "status": "PENDING",
        "due_date": datetime.now(timezone.utc),
        "channel_generated": "auto_on_registration",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    created_assessment = assessment_repo.create(assessment)
    payment_id = str(uuid.uuid4())
    payment = {
        "payment_id": payment_id,
        "assessment_id": assessment_id,
        "trader_id": assessment["trader_id"],
        "amount": 120000,
        "channel": "web",
        "payer_phone": "+233244000001",
        "momo_network": "mtn",
        "provider": "paystack",
        "provider_reference": "paystack-ref-1",
        "status": "SUCCESS",
        "failure_reason": None,
        "ip_address": "127.0.0.1",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    payment_repo.create(payment)
    fetched = payment_repo.find_by_assessment(assessment_id)

    assert created_assessment["assessment_id"] == assessment_id
    assert len(fetched) == 1
    assert fetched[0]["payment_id"] == payment_id

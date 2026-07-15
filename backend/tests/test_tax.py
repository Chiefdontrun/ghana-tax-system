import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from apps.tax.repository import (
    TaxAssessmentRepository,
    TaxPaymentRepository,
    TaxRateScheduleRepository,
)
from apps.tax.services import TaxService
from apps.tax.exceptions import RateScheduleNotFoundError, TurnoverRequiredError
from apps.registration.repository import BusinessRepository, TraderRepository


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


def test_resolve_rate_schedule_precedence(test_db):
    repo = TaxRateScheduleRepository()
    service = TaxService()

    base_doc = {
        "tax_category": "BOP",
        "business_type": "kiosk",
        "rate_type": "FIXED",
        "fixed_amount": 100,
        "effective_year": 2026,
        "is_active": True,
    }
    
    # Assembly-wide
    repo.create({**base_doc, "schedule_id": "s-assembly", "region": None, "district": None, "fixed_amount": 100})
    # Region-wide
    repo.create({**base_doc, "schedule_id": "s-region", "region": "Greater Accra", "district": None, "fixed_amount": 200})
    # District-specific
    repo.create({**base_doc, "schedule_id": "s-district", "region": "Greater Accra", "district": "Osu", "fixed_amount": 300})

    # Test Assembly-wide
    res = service.resolve_rate_schedule("kiosk", "Ashanti", "Kumasi", "BOP", 2026)
    assert res["schedule_id"] == "s-assembly"

    # Test Region-wide
    res = service.resolve_rate_schedule("kiosk", "Greater Accra", "Tema", "BOP", 2026)
    assert res["schedule_id"] == "s-region"

    # Test District-specific
    res = service.resolve_rate_schedule("kiosk", "Greater Accra", "Osu", "BOP", 2026)
    assert res["schedule_id"] == "s-district"

def test_resolve_rate_schedule_not_found(test_db):
    service = TaxService()
    with pytest.raises(RateScheduleNotFoundError):
        service.resolve_rate_schedule("unknown_type", "Ashanti", "Kumasi", "BOP", 2026)

def test_calculate_assessment_amount_fixed():
    service = TaxService()
    schedule = {"rate_type": "FIXED", "fixed_amount": 5000}
    assert service.calculate_assessment_amount(schedule) == 5000

def test_calculate_assessment_amount_percentage_turnover():
    service = TaxService()
    # Rate: 5%, min: 1000, max: 10000
    schedule = {
        "rate_type": "PERCENTAGE_TURNOVER",
        "percentage_rate": 5,
        "min_amount": 1000,
        "max_amount": 10000
    }
    
    # 5% of 50000 = 2500 (inside bounds)
    assert service.calculate_assessment_amount(schedule, 50000) == 2500
    
    # 5% of 10000 = 500 -> Clamped to min 1000
    assert service.calculate_assessment_amount(schedule, 10000) == 1000
    
    # 5% of 300000 = 15000 -> Clamped to max 10000
    assert service.calculate_assessment_amount(schedule, 300000) == 10000

def test_calculate_assessment_amount_percentage_turnover_raises_if_none():
    service = TaxService()
    schedule = {"rate_type": "PERCENTAGE_TURNOVER", "percentage_rate": 5}
    with pytest.raises(TurnoverRequiredError):
        service.calculate_assessment_amount(schedule, None)

def test_generate_assessment_idempotency(test_db):
    repo = TaxRateScheduleRepository()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()
    service = TaxService()
    
    # Create required data
    trader = trader_repo.create({
        "trader_id": "trader-idemp",
        "name": "Idemp Trader",
        "business_type": "store",
        "region": "Accra",
        "district": "Osu",
        "channel": "web",
        "status": "active"
    })
    
    biz = biz_repo.create({
        "business_id": "biz-idemp",
        "owner_trader_id": "trader-idemp",
        "business_type": "store",
    })
    
    repo.create({
        "schedule_id": "sched-1",
        "tax_category": "BOP",
        "business_type": "store",
        "region": None,
        "district": None,
        "rate_type": "FIXED",
        "fixed_amount": 5000,
        "effective_year": 2026,
        "is_active": True,
    })

    # Call generate_assessment first time
    res1 = service.generate_assessment("biz-idemp", "BOP", "2026", "admin")
    assert res1["status"] == "PENDING"
    assert res1["amount_due"] == 5000
    
    # Call generate_assessment second time with identical args
    res2 = service.generate_assessment("biz-idemp", "BOP", "2026", "admin")
    
    assert res1["assessment_id"] == res2["assessment_id"]
    
    # Verify only one row exists in db
    total = list(service.assessment_repo._col().find({"business_id": "biz-idemp"}))
    assert len(total) == 1

def test_generate_annual_assessments_batch(test_db):
    repo = TaxRateScheduleRepository()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()
    service = TaxService()
    
    # Create trader 1 (Will succeed)
    trader_repo.create({"trader_id": "t1", "business_type": "shop", "status": "active"})
    biz_repo.create({"business_id": "b1", "owner_trader_id": "t1", "business_type": "shop"})
    repo.create({
        "schedule_id": "s1", "tax_category": "BOP", "business_type": "shop", 
        "region": None, "district": None, "rate_type": "FIXED", "fixed_amount": 100,
        "effective_year": 2026, "is_active": True
    })
    
    # Create trader 2 (Needs turnover)
    trader_repo.create({"trader_id": "t2", "business_type": "factory", "status": "active"})
    biz_repo.create({"business_id": "b2", "owner_trader_id": "t2", "business_type": "factory"})
    repo.create({
        "schedule_id": "s2", "tax_category": "BOP", "business_type": "factory", 
        "region": None, "district": None, "rate_type": "PERCENTAGE_TURNOVER", "percentage_rate": 5,
        "effective_year": 2026, "is_active": True
    })

    # Create trader 3 (Missing schedule)
    trader_repo.create({"trader_id": "t3", "business_type": "missing_type", "district": "no-district", "status": "active"})
    biz_repo.create({"business_id": "b3", "owner_trader_id": "t3", "business_type": "missing_type"})
    
    # Create trader 4 (Already has assessment, should skip)
    trader_repo.create({"trader_id": "t4", "business_type": "shop", "status": "active"})
    biz_repo.create({"business_id": "b4", "owner_trader_id": "t4", "business_type": "shop"})
    service.assessment_repo.create({
        "assessment_id": "a4", "business_id": "b4", "tax_category": "BOP", "period_label": "2026"
    })

    summary = service.generate_annual_assessments_batch(2026)
    
    assert summary["created"] == 1
    assert summary["skipped_existing"] == 1
    assert summary["needs_turnover"] == ["b2"]
    assert len(summary["missing_schedule"]) == 1
    assert summary["missing_schedule"][0][0] == "b3"

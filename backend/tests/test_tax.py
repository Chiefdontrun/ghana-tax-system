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


def test_percentage_turnover_uses_bracket_2_representative_income(test_db):
    """
    PERCENTAGE_TURNOVER + BRACKET_2 representative GHC 8,400 (840000 pesewas).
    3% of 840000 = 25200, within min/max → amount_due == 25200.
    """
    from apps.tax.constants import get_representative_annual_income_pesewas

    schedule_repo = TaxRateScheduleRepository()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()
    service = TaxService()

    rep = get_representative_annual_income_pesewas("BRACKET_2")
    assert rep == 840_000

    trader_repo.create({
        "trader_id": "t-pct-b2",
        "name": "Pct Trader",
        "business_type": "clothing",
        "region": "Ashanti",
        "district": "Kumasi",
        "status": "active",
    })
    biz_repo.create({
        "business_id": "b-pct-b2",
        "owner_trader_id": "t-pct-b2",
        "business_type": "clothing",
        "income_bracket": "BRACKET_2",
    })
    schedule_repo.create({
        "schedule_id": "s-pct-b2",
        "tax_category": "BOP",
        "business_type": "clothing",
        "region": None,
        "district": None,
        "rate_type": "PERCENTAGE_TURNOVER",
        "percentage_rate": 3,
        "min_amount": 5000,
        "max_amount": 200000,
        "effective_year": 2026,
        "is_active": True,
    })

    assessment = service.generate_assessment(
        "b-pct-b2", "BOP", "2026", "admin",
        declared_turnover_pesewas=rep,
    )
    # 3% of 840000 = 25200
    assert assessment["amount_due"] == 25200


def test_fixed_schedule_under_cap_unchanged(test_db):
    """FIXED amount already under 25% of BRACKET_1 (75000) is not clamped."""
    schedule_repo = TaxRateScheduleRepository()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()
    service = TaxService()

    trader_repo.create({
        "trader_id": "t-fixed-ok",
        "business_type": "food_vendor",
        "region": "Ashanti",
        "district": "Kumasi",
        "status": "active",
    })
    biz_repo.create({
        "business_id": "b-fixed-ok",
        "owner_trader_id": "t-fixed-ok",
        "business_type": "food_vendor",
        "income_bracket": "BRACKET_1",
    })
    schedule_repo.create({
        "schedule_id": "s-fixed-ok",
        "tax_category": "BOP",
        "business_type": "food_vendor",
        "region": None,
        "district": None,
        "rate_type": "FIXED",
        "fixed_amount": 15000,  # GHC 150 < GHC 750 cap
        "effective_year": 2026,
        "is_active": True,
    })

    assessment = service.generate_assessment("b-fixed-ok", "BOP", "2026", "admin")
    assert assessment["amount_due"] == 15000
    capped_logs = list(service.audit_repo._col().find({
        "action": "ASSESSMENT_CAPPED_AFFORDABILITY",
        "details.business_id": "b-fixed-ok",
    }))
    assert len(capped_logs) == 0


def test_affordability_cap_clamps_excessive_fixed_and_audits(test_db):
    """
    FIXED GHC 2,000 (200000 pesewas) + BRACKET_1 → clamp to GHC 750 (75000).
    Assert ASSESSMENT_CAPPED_AFFORDABILITY with original/capped values.
    """
    schedule_repo = TaxRateScheduleRepository()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()
    service = TaxService()

    trader_repo.create({
        "trader_id": "t-cap-hawk",
        "name": "Hawker Cap",
        "business_type": "hawker",
        "region": "Greater Accra",
        "district": "Accra Metropolitan",
        "status": "active",
    })
    biz_repo.create({
        "business_id": "b-cap-hawk",
        "owner_trader_id": "t-cap-hawk",
        "business_type": "hawker",
        "income_bracket": "BRACKET_1",
    })
    schedule_repo.create({
        "schedule_id": "s-cap-excessive",
        "tax_category": "BOP",
        "business_type": "hawker",
        "region": None,
        "district": None,
        "rate_type": "FIXED",
        "fixed_amount": 200_000,  # GHC 2,000 — deliberately excessive
        "effective_year": 2026,
        "is_active": True,
    })

    assessment = service.generate_assessment("b-cap-hawk", "BOP", "2026", "admin")
    # 25% of GHC 3,000 = GHC 750 = 75000 pesewas
    assert assessment["amount_due"] == 75_000

    audit = service.audit_repo._col().find_one({
        "action": "ASSESSMENT_CAPPED_AFFORDABILITY",
        "details.business_id": "b-cap-hawk",
    })
    assert audit is not None
    assert audit["details"]["original_amount_due"] == 200_000
    assert audit["details"]["capped_amount_due"] == 75_000
    assert audit["details"]["income_bracket"] == "BRACKET_1"
    assert audit["details"]["schedule_id"] == "s-cap-excessive"


def test_no_income_bracket_skips_affordability_cap(test_db):
    """Pre-existing traders without income_bracket are unaffected by the cap."""
    schedule_repo = TaxRateScheduleRepository()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()
    service = TaxService()

    trader_repo.create({
        "trader_id": "t-legacy",
        "business_type": "hawker",
        "region": "Greater Accra",
        "district": "Accra Metropolitan",
        "status": "active",
    })
    # No income_bracket field (legacy)
    biz_repo.create({
        "business_id": "b-legacy",
        "owner_trader_id": "t-legacy",
        "business_type": "hawker",
    })
    schedule_repo.create({
        "schedule_id": "s-legacy-big",
        "tax_category": "BOP",
        "business_type": "hawker",
        "region": None,
        "district": None,
        "rate_type": "FIXED",
        "fixed_amount": 200_000,
        "effective_year": 2026,
        "is_active": True,
    })

    assessment = service.generate_assessment("b-legacy", "BOP", "2026", "admin")
    assert assessment["amount_due"] == 200_000
    assert service.audit_repo._col().count_documents({
        "action": "ASSESSMENT_CAPPED_AFFORDABILITY",
        "details.business_id": "b-legacy",
    }) == 0


def test_legacy_business_without_income_bracket_in_exception_queue(test_db):
    """Reports/exception queries must not break when income_bracket is absent."""
    from apps.tax.repository import TaxAssessmentExceptionRepository

    service = TaxService()
    trader_repo = TraderRepository()
    biz_repo = BusinessRepository()

    trader_repo.create({
        "trader_id": "t-exc-legacy",
        "business_type": "artisan",
        "region": "Volta",
        "district": "Ho",
        "status": "active",
    })
    biz_repo.create({
        "business_id": "b-exc-legacy",
        "owner_trader_id": "t-exc-legacy",
        "business_type": "artisan",
        # no income_bracket
    })
    service.log_assessment_exception("b-exc-legacy", "BOP", "2026", "MISSING_SCHEDULE")
    exc_repo = TaxAssessmentExceptionRepository()
    rows = list(exc_repo._col().find({"business_id": "b-exc-legacy"}, {"_id": 0}))
    assert len(rows) == 1
    assert rows[0]["exception_type"] == "MISSING_SCHEDULE"
    # income_bracket not required on exception docs
    assert "income_bracket" not in rows[0] or rows[0].get("income_bracket") is None


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

"""Service layer for tax assessment and payment foundations."""

from __future__ import annotations

import logging
import uuid
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from apps.tax.repository import (
    TaxAssessmentRepository,
    TaxPaymentRepository,
    TaxRateScheduleRepository,
    TaxAssessmentExceptionRepository,
)
from apps.registration.repository import BusinessRepository, TraderRepository
from apps.audit.repository import AuditRepository
from apps.tax.exceptions import RateScheduleNotFoundError, TurnoverRequiredError
from apps.tax.constants import affordability_cap_pesewas

logger = logging.getLogger(__name__)


class TaxService:
    """Service layer for the tax module."""

    def __init__(self):
        self.schedule_repo = TaxRateScheduleRepository()
        self.assessment_repo = TaxAssessmentRepository()
        self.payment_repo = TaxPaymentRepository()
        self.exception_repo = TaxAssessmentExceptionRepository()
        self.business_repo = BusinessRepository()
        self.trader_repo = TraderRepository()
        self.audit_repo = AuditRepository()

    def resolve_rate_schedule(
        self,
        business_type: str,
        region: Optional[str],
        district: Optional[str],
        tax_category: str,
        year: int,
    ) -> dict:
        """
        Resolve the most specific active schedule for the supplied business context.
        Raises RateScheduleNotFoundError if none is found.
        """
        query = {
            "tax_category": tax_category,
            "business_type": business_type,
            "effective_year": year,
            "is_active": True,
        }
        
        # In mongo, we can just fetch all matching category/type/year/active and filter in Python
        # or we can do a complex $or. Filtering in Python is fine since the number of active schedules
        # for a specific category/type/year is very small (often 1-5).
        candidates = list(self.schedule_repo._col().find(query, {"_id": 0}))
        
        valid_matches = []
        for c in candidates:
            c_region = c.get("region")
            c_district = c.get("district")
            
            # A schedule matches if its region/district is either None (applies to all) or exactly matches the input
            if c_region is not None and c_region != region:
                continue
            if c_district is not None and c_district != district:
                continue
            
            valid_matches.append(c)

        if not valid_matches:
            raise RateScheduleNotFoundError(
                f"No active rate schedule found for {business_type} in {district}, {region} "
                f"for {tax_category} ({year})."
            )

        def specificity(score: dict) -> tuple[int, int, int]:
            # Tuple comparison: (district_match, region_match, assembly_match)
            # Higher tuple wins.
            district_match = 1 if score.get("district") is not None else 0
            region_match = 1 if score.get("region") is not None else 0
            assembly_match = 1 if score.get("district") is None and score.get("region") is None else 0
            return (district_match, region_match, assembly_match)

        return max(valid_matches, key=specificity)

    def calculate_assessment_amount(
        self,
        schedule: dict,
        declared_turnover_pesewas: Optional[int] = None,
        income_bracket: Optional[str] = None,
        business_id: Optional[str] = None,
    ) -> int:
        """
        Calculate assessment amount based on schedule rules.
        Returns amount in pesewas.

        When income_bracket is set, applies a hard affordability cap of 25% of
        the bracket's representative annual income (both FIXED and
        PERCENTAGE_TURNOVER). Pre-existing businesses with no bracket skip the cap.
        """
        rate_type = schedule.get("rate_type")
        
        if rate_type == "FIXED":
            amount = schedule["fixed_amount"]
        elif rate_type == "PERCENTAGE_TURNOVER":
            if declared_turnover_pesewas is None:
                raise TurnoverRequiredError("Declared turnover is required for PERCENTAGE_TURNOVER schedule.")
                
            percentage_rate = schedule.get("percentage_rate", 0)
            
            # Calculate (turnover * rate / 100) using Decimal for exact rounding
            # percentage_rate is e.g. 5.5 for 5.5%
            turnover_dec = Decimal(declared_turnover_pesewas)
            rate_dec = Decimal(str(percentage_rate))
            
            calculated_amount = (turnover_dec * rate_dec / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            amount = int(calculated_amount)
            
            min_amount = schedule.get("min_amount")
            max_amount = schedule.get("max_amount")
            
            if min_amount is not None and amount < min_amount:
                amount = min_amount
            if max_amount is not None and amount > max_amount:
                amount = max_amount
        else:
            raise ValueError(f"Unknown rate_type: {rate_type}")

        # Hard affordability cap — unconditional for any rate type when bracket is known
        cap = affordability_cap_pesewas(income_bracket)
        if cap is not None and amount > cap:
            original_amount = amount
            amount = cap
            self.audit_repo.log({
                "action": "ASSESSMENT_CAPPED_AFFORDABILITY",
                "entity_type": "tax_assessment",
                "entity_id": business_id or schedule.get("schedule_id", ""),
                "actor_type": "system",
                "channel": "tax_engine",
                "details": {
                    "business_id": business_id,
                    "original_amount_due": original_amount,
                    "capped_amount_due": amount,
                    "income_bracket": income_bracket,
                    "schedule_id": schedule.get("schedule_id"),
                },
            })

        return amount

    def generate_assessment(
        self,
        business_id: str,
        tax_category: str,
        period_label: str,
        channel_generated: str,
        declared_turnover_pesewas: Optional[int] = None,
        audit_log: bool = True,
        actor_id: str = None,
    ) -> dict:
        """
        Generate an assessment for a business.
        Idempotent: returns existing assessment if one already exists for the same period.
        """
        # Idempotency check
        existing = self.assessment_repo._col().find_one({
            "business_id": business_id,
            "tax_category": tax_category,
            "period_label": period_label
        }, {"_id": 0})
        
        if existing:
            logger.debug(
                "Assessment already exists for business %s, category %s, period %s",
                business_id, tax_category, period_label
            )
            return existing

        business = self.business_repo._col().find_one({"business_id": business_id})
        if not business:
            raise ValueError(f"Business not found: {business_id}")

        # The location might be referenced by location_id, or we might need the trader's location data.
        # Let's fetch trader to get region/district.
        trader_id = business["owner_trader_id"]
        trader = self.trader_repo.find_by_id(trader_id)
        if not trader:
            raise ValueError(f"Trader not found: {trader_id}")

        region = trader.get("region")
        district = trader.get("district")
        business_type = business.get("business_type")
        
        try:
            year = int(period_label)
        except ValueError:
            # fallback if period_label is not a year
            year = datetime.now(timezone.utc).year

        schedule = self.resolve_rate_schedule(
            business_type=business_type,
            region=region,
            district=district,
            tax_category=tax_category,
            year=year
        )

        # Nullable on legacy businesses — cap only when present
        income_bracket = business.get("income_bracket")

        amount_due = self.calculate_assessment_amount(
            schedule,
            declared_turnover_pesewas,
            income_bracket=income_bracket,
            business_id=business_id,
        )

        # Set due date convention: Dec 31 of the year for BOP
        if tax_category == "BOP":
            due_date = datetime(year, 12, 31, tzinfo=timezone.utc)
        else:
            # Fallback for others, though currently only BOP
            due_date = datetime(year, 12, 31, tzinfo=timezone.utc)

        assessment_id = str(uuid.uuid4())
        assessment_doc = {
            "assessment_id": assessment_id,
            "business_id": business_id,
            "trader_id": trader_id,
            "tax_category": tax_category,
            "period_label": period_label,
            "schedule_id": schedule["schedule_id"],
            "amount_due": amount_due,
            "amount_paid": 0,
            "status": "PENDING",
            "due_date": due_date,
            "channel_generated": channel_generated
        }
        
        created_doc = self.assessment_repo.create(assessment_doc)

        if actor_id is None:
            actor_id = "system" if channel_generated == "auto_on_registration" else "admin"

        if audit_log:
            self.audit_repo.log({
                "action": "ASSESSMENT_GENERATED",
                "entity_type": "tax_assessment",
                "entity_id": assessment_id,
                "actor_type": "system" if actor_id == "system" else "admin",
                "actor_id": actor_id,
                "channel": channel_generated,
                "details": {
                    "business_id": business_id,
                    "amount_due": amount_due,
                    "period_label": period_label
                }
            })

        return created_doc

    def log_assessment_exception(
        self, business_id: str, tax_category: str, period_label: str, exception_type: str
    ) -> None:
        """Durably log an exception for unresolved assessment generation."""
        existing = self.exception_repo._col().find_one({
            "business_id": business_id,
            "tax_category": tax_category,
            "period_label": period_label,
            "exception_type": exception_type,
            "status": "OPEN"
        }, {"_id": 0})
        
        if existing:
            return

        business = self.business_repo._col().find_one({"business_id": business_id})
        trader_id = business["owner_trader_id"]
        trader = self.trader_repo.find_by_id(trader_id)
        
        doc = {
            "exception_id": str(uuid.uuid4()),
            "business_id": business_id,
            "trader_id": trader_id,
            "tax_category": tax_category,
            "period_label": period_label,
            "exception_type": exception_type,
            "business_type": business.get("business_type"),
            "region": trader.get("region"),
            "district": trader.get("district"),
            "status": "OPEN",
            "resolved_by": None,
            "resolved_at": None,
        }
        self.exception_repo.create(doc)

    def generate_annual_assessments_batch(self, year: int, admin_id: str = "admin") -> dict:
        """
        Batch generate assessments for all active traders' businesses for a given year.
        Returns a summary dict.
        """
        created = 0
        skipped_existing = 0
        needs_turnover = []
        missing_schedule = []

        # List all active traders.
        # list_with_filters expects a limit, let's paginate or fetch all.
        limit = 1000
        skip = 0
        
        while True:
            traders, total = self.trader_repo.list_with_filters({"status": "active"}, skip=skip, limit=limit)
            if not traders:
                break
                
            for trader in traders:
                # Get business for trader
                business = self.business_repo.find_by_owner(trader["trader_id"])
                if not business:
                    continue
                    
                # generate_assessment does an idempotency check, but it returns the document.
                # To count skipped vs created, we can check if it already existed.
                # Actually, an easier way is to check idempotency before, or look at the created_at.
                # Let's check idempotency first to safely count it.
                existing = self.assessment_repo._col().find_one({
                    "business_id": business["business_id"],
                    "tax_category": "BOP",
                    "period_label": str(year)
                }, {"_id": 0})
                
                if existing:
                    skipped_existing += 1
                    continue
                    
                try:
                    self.generate_assessment(
                        business_id=business["business_id"],
                        tax_category="BOP",
                        period_label=str(year),
                        channel_generated="admin_batch",
                        audit_log=False,
                        actor_id=admin_id,
                    )
                    created += 1
                except TurnoverRequiredError:
                    self.log_assessment_exception(business["business_id"], "BOP", str(year), "NEEDS_TURNOVER")
                    needs_turnover.append(business["business_id"])
                except RateScheduleNotFoundError:
                    self.log_assessment_exception(business["business_id"], "BOP", str(year), "MISSING_SCHEDULE")
                    missing_schedule.append((business["business_id"], business.get("business_type"), trader.get("district")))
                except Exception as e:
                    logger.error(f"Error generating assessment for business {business['business_id']}: {e}")

            skip += limit

        self.audit_repo.log({
            "action": "ASSESSMENT_GENERATED",
            "entity_type": "batch",
            "entity_id": str(year),
            "actor_type": "admin",
            "actor_id": admin_id,
            "channel": "admin_batch",
            "details": {
                "created_count": created,
                "skipped_count": skipped_existing,
                "year": year
            }
        })

        return {
            "created": created,
            "skipped_existing": skipped_existing,
            "needs_turnover": needs_turnover,
            "missing_schedule": missing_schedule
        }

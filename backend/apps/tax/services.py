"""Service layer for tax assessment and payment foundations."""

from __future__ import annotations

from typing import Optional

from apps.tax.repository import (
    TaxAssessmentRepository,
    TaxPaymentRepository,
    TaxRateScheduleRepository,
)


class TaxService:
    """Simple service layer scaffold for the tax module."""

    def __init__(self):
        self.schedule_repo = TaxRateScheduleRepository()
        self.assessment_repo = TaxAssessmentRepository()
        self.payment_repo = TaxPaymentRepository()

    def resolve_rate_schedule(
        self,
        business_type: str,
        region: Optional[str],
        district: Optional[str],
        tax_category: str,
        year: int,
    ) -> Optional[dict]:
        """Resolve the most specific active schedule for the supplied business context."""
        # Placeholder implementation for Step A1; this is intentionally simple and
        # will be expanded by the assessment engine in later steps.
        query = {
            "tax_category": tax_category,
            "business_type": business_type,
            "effective_year": year,
            "is_active": True,
        }
        matches = list(self.schedule_repo._col().find(query, {"_id": 0}))
        if not matches:
            return None

        def specificity(score: dict) -> tuple[int, int, int]:
            district_match = 1 if district and score.get("district") == district else 0
            region_match = 1 if region and score.get("region") == region else 0
            assembly_match = 1 if not score.get("district") and not score.get("region") else 0
            return (district_match, region_match, assembly_match)

        return max(matches, key=specificity)

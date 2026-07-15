"""
Tax repositories for tax rate schedules, assessments, and payments.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from pymongo import DESCENDING

from core.utils.mongo import (
    get_collection,
    TAX_RATE_SCHEDULES,
    TAX_ASSESSMENTS,
    TAX_PAYMENTS,
)

logger = logging.getLogger(__name__)


class TaxRateScheduleRepository:
    """CRUD for tax_rate_schedules."""

    def _col(self):
        return get_collection(TAX_RATE_SCHEDULES)

    def create(self, schedule_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        doc = {**schedule_data, "created_at": now, "updated_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def find_by_id(self, schedule_id: str) -> Optional[dict]:
        return self._col().find_one({"schedule_id": schedule_id}, {"_id": 0})


class TaxAssessmentRepository:
    """CRUD for tax_assessments."""

    def _col(self):
        return get_collection(TAX_ASSESSMENTS)

    def create(self, assessment_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        doc = {**assessment_data, "created_at": now, "updated_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def find_by_id(self, assessment_id: str) -> Optional[dict]:
        return self._col().find_one({"assessment_id": assessment_id}, {"_id": 0})

    def list_for_trader(self, trader_id: str) -> list[dict]:
        return list(
            self._col()
            .find({"trader_id": trader_id}, {"_id": 0})
            .sort("created_at", DESCENDING)
        )


class TaxPaymentRepository:
    """CRUD for tax_payments."""

    def _col(self):
        return get_collection(TAX_PAYMENTS)

    def create(self, payment_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        doc = {**payment_data, "created_at": now, "updated_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def find_by_assessment(self, assessment_id: str) -> list[dict]:
        return list(
            self._col().find({"assessment_id": assessment_id}, {"_id": 0}).sort("created_at", DESCENDING)
        )

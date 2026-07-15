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
    TAX_ASSESSMENT_EXCEPTIONS,
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

    def find_by_id(self, payment_id: str) -> Optional[dict]:
        return self._col().find_one({"payment_id": payment_id}, {"_id": 0})

    def update(self, payment_id: str, updates: dict) -> Optional[dict]:
        updates["updated_at"] = datetime.now(timezone.utc)
        self._col().update_one({"payment_id": payment_id}, {"$set": updates})
        return self.find_by_id(payment_id)

class TaxAssessmentExceptionRepository:
    """CRUD for tax_assessment_exceptions."""

    def _col(self):
        return get_collection(TAX_ASSESSMENT_EXCEPTIONS)

    def create(self, exception_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        doc = {**exception_data, "created_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def find_by_id(self, exception_id: str) -> Optional[dict]:
        return self._col().find_one({"exception_id": exception_id}, {"_id": 0})

    def update(self, exception_id: str, updates: dict) -> Optional[dict]:
        self._col().update_one({"exception_id": exception_id}, {"$set": updates})
        return self.find_by_id(exception_id)

    def list_with_filters(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        query = {}
        if filters.get("exception_type"):
            query["exception_type"] = filters["exception_type"]
        if filters.get("status"):
            query["status"] = filters["status"]
        if filters.get("business_type"):
            query["business_type"] = filters["business_type"]
        if filters.get("district"):
            query["district"] = {"$regex": filters["district"], "$options": "i"}

        total = self._col().count_documents(query)
        cursor = (
            self._col().find(query, {"_id": 0})
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

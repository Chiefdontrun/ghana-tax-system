"""
TraderOTPRepository — MongoDB persistence for trader login OTPs.
"""

from datetime import datetime, timezone
from typing import Optional

from pymongo import ASCENDING, DESCENDING

from core.utils.mongo import get_collection, TRADER_OTP_VERIFICATIONS


class TraderOTPRepository:
    """Read/write helpers for the trader_otp_verifications collection."""

    def _col(self):
        col = get_collection(TRADER_OTP_VERIFICATIONS)
        self.ensure_indexes(col)
        return col

    @staticmethod
    def ensure_indexes(col=None) -> None:
        collection = col if col is not None else get_collection(TRADER_OTP_VERIFICATIONS)
        collection.create_index([("otp_id", ASCENDING)], unique=True)
        collection.create_index([("phone_number", ASCENDING), ("created_at", DESCENDING)])
        collection.create_index("expires_at", expireAfterSeconds=0)

    def create(self, doc: dict) -> dict:
        now = datetime.now(timezone.utc)
        record = {
            **doc,
            "attempts": doc.get("attempts", 0),
            "resend_count": doc.get("resend_count", 0),
            "created_at": doc.get("created_at", now),
            "used_at": doc.get("used_at"),
            "invalidated_at": doc.get("invalidated_at"),
        }
        self._col().insert_one(record)
        record.pop("_id", None)
        return record

    def find_active(self, phone_number: str) -> Optional[dict]:
        """Find the most recent non-invalidated, non-expired OTP for a phone number."""
        return self._col().find_one(
            {
                "phone_number": phone_number,
                "used_at": None,
                "invalidated_at": None,
            },
            {"_id": 0},
            sort=[("created_at", DESCENDING)],
        )

    def latest_for_phone(self, phone_number: str) -> Optional[dict]:
        return self._col().find_one(
            {"phone_number": phone_number},
            {"_id": 0},
            sort=[("created_at", DESCENDING)],
        )

    def increment_attempts(self, otp_id: str) -> None:
        self._col().update_one(
            {"otp_id": otp_id},
            {"$inc": {"attempts": 1}},
        )

    def mark_used(self, otp_id: str) -> None:
        self._col().update_one(
            {"otp_id": otp_id},
            {"$set": {"used_at": datetime.now(timezone.utc)}},
        )

    def invalidate(self, otp_id: str) -> None:
        self._col().update_one(
            {"otp_id": otp_id},
            {"$set": {"invalidated_at": datetime.now(timezone.utc)}},
        )

    def invalidate_active_for_phone(self, phone_number: str) -> None:
        self._col().update_many(
            {
                "phone_number": phone_number,
                "used_at": None,
                "invalidated_at": None,
            },
            {"$set": {"invalidated_at": datetime.now(timezone.utc)}},
        )

    def cleanup_expired_or_used(self) -> int:
        now = datetime.now(timezone.utc)
        result = self._col().delete_many(
            {
                "$or": [
                    {"expires_at": {"$lte": now}},
                    {"used_at": {"$ne": None}},
                    {"invalidated_at": {"$ne": None}},
                ]
            }
        )
        return result.deleted_count

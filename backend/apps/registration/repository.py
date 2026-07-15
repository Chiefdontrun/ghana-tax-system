"""
Repositories for the registration app:
  - TraderRepository   (traders collection)
  - BusinessRepository (businesses collection)
  - LocationRepository (locations collection)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from pymongo import DESCENDING

from core.utils.mongo import get_collection, TRADERS, BUSINESSES, LOCATIONS

logger = logging.getLogger(__name__)


# ── TraderRepository ──────────────────────────────────────────────────────────

class TraderRepository:
    """CRUD + filtered queries for the traders collection."""

    def _col(self):
        return get_collection(TRADERS)

    # ── Reads ──────────────────────────────────────────────────────────────────

    def find_by_phone(self, phone: str) -> Optional[dict]:
        return self._col().find_one({"phone_number": phone}, {"_id": 0})

    def find_by_tin(self, tin: str) -> Optional[dict]:
        return self._col().find_one({"tin_number": tin}, {"_id": 0})

    def find_by_id(self, trader_id: str) -> Optional[dict]:
        return self._col().find_one({"trader_id": trader_id}, {"_id": 0})

    def list_with_filters(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Return (page_of_docs, total_matching_count).
        Supported filter keys: channel, business_type, region, district,
        date_from (datetime), date_to (datetime), search (str).
        """
        query = self._build_query(filters)
        col = self._col()
        total = col.count_documents(query)
        cursor = (
            col.find(query, {"_id": 0})
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return list(cursor), total

    def count_by_channel(self) -> dict:
        """Return {web: N, ussd: N}."""
        pipeline = [
            {"$group": {"_id": "$channel", "count": {"$sum": 1}}},
        ]
        result = {}
        for doc in self._col().aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result

    def count_by_date_range(self, start: datetime, end: datetime) -> int:
        return self._col().count_documents(
            {"created_at": {"$gte": start, "$lte": end}}
        )

    # ── Writes ─────────────────────────────────────────────────────────────────

    def create(self, trader_data: dict) -> dict:
        """Insert a new trader document. Returns doc without _id."""
        now = datetime.now(timezone.utc)
        doc = {**trader_data, "created_at": now, "updated_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def update(self, trader_id: str, update_data: dict) -> None:
        """Update fields on a trader document."""
        self._col().update_one(
            {"trader_id": trader_id},
            {"$set": update_data}
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_query(filters: dict) -> dict:
        query: dict = {}

        if filters.get("channel"):
            query["channel"] = filters["channel"]

        if filters.get("business_type"):
            query["business_type"] = filters["business_type"]

        if filters.get("region"):
            query["region"] = {"$regex": filters["region"], "$options": "i"}

        if filters.get("district"):
            query["district"] = {"$regex": filters["district"], "$options": "i"}

        date_filter: dict = {}
        if filters.get("date_from"):
            date_filter["$gte"] = filters["date_from"]
        if filters.get("date_to"):
            date_filter["$lte"] = filters["date_to"]
        if date_filter:
            query["created_at"] = date_filter

        if filters.get("search"):
            term = filters["search"]
            query["$or"] = [
                {"name": {"$regex": term, "$options": "i"}},
                {"phone_number": {"$regex": term, "$options": "i"}},
                {"tin_number": {"$regex": term, "$options": "i"}},
            ]

        return query


# ── BusinessRepository ────────────────────────────────────────────────────────

class BusinessRepository:
    """CRUD for the businesses collection."""

    def _col(self):
        return get_collection(BUSINESSES)

    def create(self, business_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        doc = {**business_data, "created_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def find_by_owner(self, trader_id: str) -> Optional[dict]:
        return self._col().find_one({"owner_trader_id": trader_id}, {"_id": 0})


# ── LocationRepository ────────────────────────────────────────────────────────

class LocationRepository:
    """CRUD + list helpers for the locations collection."""

    def _col(self):
        return get_collection(LOCATIONS)

    def create(self, location_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        doc = {**location_data, "created_at": now}
        self._col().insert_one(doc)
        doc.pop("_id", None)
        return doc

    def find_by_id(self, location_id: str) -> Optional[dict]:
        return self._col().find_one({"location_id": location_id}, {"_id": 0})

    def find_or_create(self, region: str, district: str, market_name: str) -> dict:
        """
        Return existing location or create a new one.
        Matches on (region, district, market_name) — case-insensitive.
        """
        import uuid
        existing = self._col().find_one(
            {
                "region": {"$regex": f"^{region}$", "$options": "i"},
                "district": {"$regex": f"^{district}$", "$options": "i"},
                "market_name": {"$regex": f"^{market_name}$", "$options": "i"},
            },
            {"_id": 0},
        )
        if existing:
            return existing
        return self.create(
            {
                "location_id": str(uuid.uuid4()),
                "region": region,
                "district": district,
                "market_name": market_name,
            }
        )

    def list_districts(self) -> list[str]:
        return self._col().distinct("district")

    def list_regions(self) -> list[str]:
        return self._col().distinct("region")

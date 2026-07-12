"""
ReportsService — orchestrates aggregation queries and CSV export.
Business logic lives here; views stay thin.

Phase 12 additions:
  - Redis caching on get_summary() with configurable TTL (REPORTS_CACHE_TTL)
  - Service-layer RBAC assertion guards (defence-in-depth beyond view layer)
  - Audit logging for duplicate-phone idempotency events
"""

import csv
import io
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from django.core.cache import cache
from django.conf import settings

from apps.audit.repository import AuditRepository
from apps.registration.repository import TraderRepository
from apps.reports.repository import ReportsRepository

logger = logging.getLogger(__name__)

_reports_repo = ReportsRepository()
_trader_repo = TraderRepository()
_audit_repo = AuditRepository()

# CSV column definitions: (header_label, document_field)
CSV_COLUMNS = [
    ("TIN", "tin_number"),
    ("Name", "name"),
    ("Phone", "phone_number"),
    ("Business Type", "business_type"),
    ("Region", "region"),
    ("District", "district"),
    ("Market", "market_name"),
    ("Channel", "channel"),
    ("Registered At", "created_at"),
]


def _period_to_date_filter(period: str) -> Optional[dict]:
    """Convert a period string ('7d', '30d', 'all') to a MongoDB date filter dict."""
    now = datetime.now(timezone.utc)
    if period == "7d":
        return {"$gte": now - timedelta(days=7)}
    elif period == "30d":
        return {"$gte": now - timedelta(days=30)}
    return None  # 'all' — no date filter


def _build_filter_dict(validated: dict) -> dict:
    """
    Build a filters dict compatible with TraderRepository._build_query()
    from validated query params (may include period, date_from, date_to, etc.).
    """
    filters: dict = {}

    if validated.get("channel"):
        filters["channel"] = validated["channel"]
    if validated.get("business_type"):
        filters["business_type"] = validated["business_type"]
    if validated.get("region"):
        filters["region"] = validated["region"]
    if validated.get("district"):
        filters["district"] = validated["district"]
    if validated.get("search"):
        filters["search"] = validated["search"]

    # Date range: period shorthand takes precedence over explicit dates
    period = validated.get("period")
    if period and period != "all":
        date_filter = _period_to_date_filter(period)
        if date_filter:
            filters["date_from"] = date_filter.get("$gte")
    else:
        if validated.get("date_from"):
            filters["date_from"] = datetime.combine(
                validated["date_from"], datetime.min.time()
            ).replace(tzinfo=timezone.utc)
        if validated.get("date_to"):
            filters["date_to"] = datetime.combine(
                validated["date_to"], datetime.max.time()
            ).replace(tzinfo=timezone.utc)

    return filters


class ReportsService:

    def get_summary(self, period: str, actor: dict) -> dict:
        """
        Build the full reports summary payload.
        Uses MongoDB aggregation pipelines exclusively — no Python-level loops.

        Phase 12: Results are cached in Redis with a configurable TTL
        (default 45s, overridden by REPORTS_CACHE_TTL env var).
        Cache key is scoped to the period so 7d / 30d / all are cached separately.
        Service-layer RBAC guard: actor must be TAX_ADMIN or SYS_ADMIN.
        """
        # ── Service-layer RBAC guard (defence-in-depth) ───────────────────────
        actor_role = actor.get("role", "")
        if actor_role not in ("TAX_ADMIN", "SYS_ADMIN"):
            raise PermissionError(f"Insufficient role '{actor_role}' for reports access.")

        # ── Cache lookup ──────────────────────────────────────────────────────
        cache_key = f"reports_summary_{period}"
        try:
            cached = cache.get(cache_key)
        except Exception as cache_err:
            logger.warning(
                "Reports cache read failed for %s: %s",
                cache_key,
                cache_err,
            )
            cached = None

        if cached is not None:
            logger.debug("Cache HIT for reports summary (period=%s)", period)
            # Update generated_at to reflect when the cache was served
            cached["served_from_cache"] = True
            return cached

        logger.debug("Cache MISS for reports summary (period=%s) — running aggregations", period)

        date_filter = _period_to_date_filter(period)
        now = datetime.now(timezone.utc)

        kpis = _reports_repo.kpi_totals()
        by_channel = _reports_repo.summary_by_channel(date_filter)
        by_business_type = _reports_repo.summary_by_business_type(date_filter)
        by_location = _reports_repo.summary_by_location(date_filter)
        daily_days = 7 if period == "7d" else 30
        daily_trend = _reports_repo.daily_registrations(daily_days)

        # Flatten channel list → {web: N, ussd: N} dict
        channel_dict = {item["channel"]: item["count"] for item in by_channel}

        # Total within the requested period
        period_total = sum(item["count"] for item in by_channel)

        result = {
            "total_traders": kpis["total_traders"],
            "today_registrations": kpis["today_registrations"],
            "period": period,
            "period_total": period_total,
            "by_channel": channel_dict,
            "by_business_type": by_business_type,
            "by_region": [
                {"region": r.get("region", ""), "count": r["count"]}
                for r in by_location
            ],
            "daily_trend": daily_trend,
            "generated_at": now.isoformat(),
            "served_from_cache": False,
        }

        # ── Cache write ───────────────────────────────────────────────────────
        ttl = getattr(settings, "REPORTS_CACHE_TTL", 45)
        try:
            cache.set(cache_key, result, timeout=ttl)
        except Exception as cache_err:
            # Never let a cache write failure break the response
            logger.warning("Cache write failed for reports summary: %s", cache_err)

        return result

    def get_traders_list(self, validated_params: dict, actor: dict = None) -> dict:
        """
        Return paginated traders list with filter support.
        Phase 12: Optional actor for service-layer RBAC guard.
        """
        # Service-layer RBAC guard (defence-in-depth)
        if actor is not None:
            actor_role = actor.get("role", "")
            if actor_role not in ("TAX_ADMIN", "SYS_ADMIN"):
                raise PermissionError(f"Insufficient role '{actor_role}' for traders access.")
        page = validated_params.get("page", 1)
        page_size = validated_params.get("page_size", 20)
        skip = (page - 1) * page_size

        filters = _build_filter_dict(validated_params)
        traders, total = _trader_repo.list_with_filters(filters, skip=skip, limit=page_size)

        # Serialise datetime fields
        for t in traders:
            if isinstance(t.get("created_at"), datetime):
                t["created_at"] = t["created_at"].isoformat()

        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "traders": traders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_trader_detail(self, trader_id: str, actor: dict = None) -> Optional[dict]:
        """Return full trader detail including business info.
        Phase 12: Optional actor for service-layer RBAC guard.
        """
        if actor is not None:
            actor_role = actor.get("role", "")
            if actor_role not in ("TAX_ADMIN", "SYS_ADMIN"):
                raise PermissionError(f"Insufficient role '{actor_role}' for trader detail access.")
        from apps.registration.repository import BusinessRepository
        trader = _trader_repo.find_by_id(trader_id)
        if not trader:
            return None

        # Attach business info if available
        biz_repo = BusinessRepository()
        business = biz_repo.find_by_owner(trader_id)
        if business:
            trader["business"] = business

        if isinstance(trader.get("created_at"), datetime):
            trader["created_at"] = trader["created_at"].isoformat()

        return trader

    def export_csv(self, validated_params: dict, actor: dict, ip_address: str) -> str:
        """
        Build a CSV string of all matching traders.
        Writes an EXPORT_REPORT audit log entry.
        Returns the CSV content as a string.
        Phase 12: Service-layer RBAC guard.
        """
        # Service-layer RBAC guard (defence-in-depth)
        actor_role = actor.get("role", "")
        if actor_role not in ("TAX_ADMIN", "SYS_ADMIN"):
            raise PermissionError(f"Insufficient role '{actor_role}' for CSV export.")
        filters = _build_filter_dict(validated_params)
        rows = _reports_repo.export_traders_csv(filters)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([col[0] for col in CSV_COLUMNS])

        # Data rows
        for row in rows:
            writer.writerow([
                row.get(field, "") if not isinstance(row.get(field), datetime)
                else row[field].strftime("%Y-%m-%d %H:%M:%S")
                for _, field in CSV_COLUMNS
            ])

        _audit_repo.log({
            "event_id": str(uuid.uuid4()),
            "actor_id": actor.get("admin_id", "unknown"),
            "actor_role": actor.get("role", "unknown"),
            "action": "EXPORT_REPORT",
            "entity_type": "report",
            "channel": "admin",
            "ip_address": ip_address,
            "details": {
                "filters": {k: str(v) for k, v in filters.items()},
                "row_count": len(rows),
            },
        })

        return output.getvalue()

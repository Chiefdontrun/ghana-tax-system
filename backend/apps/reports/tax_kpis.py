"""
Tax KPI aggregation helpers for reports (Phase F1).

All money is stored as integer pesewas; conversion to GHS happens only at
response boundary (divide by 100). Historical assessments are never re-rated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from core.utils.mongo import get_collection, TAX_ASSESSMENTS, TAX_PAYMENTS, TRADERS


def _pesewas_to_ghs(pesewas: int | float | None) -> float:
    return round((pesewas or 0) / 100.0, 2)


def build_assessment_match(
    *,
    period_label: Optional[str] = None,
    business_type: Optional[str] = None,
    region: Optional[str] = None,
    district: Optional[str] = None,
) -> dict:
    """Mongo match for tax_assessments (optional filters)."""
    match: dict[str, Any] = {}
    if period_label:
        match["period_label"] = period_label
    if business_type:
        match["business_type"] = business_type
    if region:
        match["region"] = region
    if district:
        match["district"] = district
    return match


def aggregate_tax_kpis(
    *,
    period_label: Optional[str] = None,
    business_type: Optional[str] = None,
    region: Optional[str] = None,
    district: Optional[str] = None,
) -> dict:
    """
    Return tax KPI block:
      total_assessed_ghs, total_collected_ghs, collection_rate_pct,
      overdue_count, by_business_type[], by_region[], by_district[]
    """
    col = get_collection(TAX_ASSESSMENTS)
    match = build_assessment_match(
        period_label=period_label,
        business_type=business_type,
        region=region,
        district=district,
    )

    pipeline: list[dict] = []
    if match:
        pipeline.append({"$match": match})
    pipeline.append({
        "$group": {
            "_id": None,
            "total_assessed": {"$sum": {"$ifNull": ["$amount_due", 0]}},
            "total_collected": {"$sum": {"$ifNull": ["$amount_paid", 0]}},
            "count": {"$sum": 1},
        }
    })
    totals = list(col.aggregate(pipeline))
    if totals:
        assessed = int(totals[0].get("total_assessed") or 0)
        collected = int(totals[0].get("total_collected") or 0)
    else:
        assessed = 0
        collected = 0

    rate = (collected / assessed * 100.0) if assessed > 0 else 0.0

    now = datetime.now(timezone.utc)
    overdue_query = {
        **match,
        "status": {"$in": ["PENDING", "PARTIAL"]},
        "due_date": {"$lt": now},
    }
    overdue_count = col.count_documents(overdue_query)

    def _group_by(field: str) -> list[dict]:
        p: list[dict] = []
        if match:
            p.append({"$match": match})
        p.extend([
            {
                "$group": {
                    "_id": {"$ifNull": [f"${field}", ""]},
                    "total_assessed": {"$sum": {"$ifNull": ["$amount_due", 0]}},
                    "total_collected": {"$sum": {"$ifNull": ["$amount_paid", 0]}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"total_assessed": -1}},
        ])
        rows = []
        for r in col.aggregate(p):
            a = int(r.get("total_assessed") or 0)
            c = int(r.get("total_collected") or 0)
            rows.append({
                field: r["_id"] or "",
                "total_assessed_ghs": _pesewas_to_ghs(a),
                "total_collected_ghs": _pesewas_to_ghs(c),
                "collection_rate_pct": round((c / a * 100.0) if a > 0 else 0.0, 2),
                "count": r.get("count", 0),
            })
        return rows

    return {
        "total_assessed_ghs": _pesewas_to_ghs(assessed),
        "total_collected_ghs": _pesewas_to_ghs(collected),
        "collection_rate_pct": round(rate, 2),
        "overdue_count": overdue_count,
        "assessment_count": (totals[0].get("count") if totals else 0) or 0,
        "by_business_type": _group_by("business_type"),
        "by_region": _group_by("region"),
        "by_district": _group_by("district"),
        "filters": {
            "period_label": period_label,
            "business_type": business_type,
            "region": region,
            "district": district,
        },
        # Raw pesewas for internal tests / exact math
        "_total_assessed_pesewas": assessed,
        "_total_collected_pesewas": collected,
    }


def export_tax_assessments_csv_rows(filters: dict) -> list[dict]:
    """Join assessments with trader names for CSV export."""
    match = build_assessment_match(
        period_label=filters.get("period_label"),
        business_type=filters.get("business_type"),
        region=filters.get("region"),
        district=filters.get("district"),
    )
    if filters.get("status"):
        match["status"] = filters["status"]

    assessments = list(
        get_collection(TAX_ASSESSMENTS)
        .find(match, {"_id": 0})
        .sort("created_at", -1)
        .limit(10000)
    )
    trader_ids = list({a.get("trader_id") for a in assessments if a.get("trader_id")})
    traders = {
        t["trader_id"]: t
        for t in get_collection(TRADERS).find(
            {"trader_id": {"$in": trader_ids}},
            {"_id": 0, "trader_id": 1, "name": 1, "business_type": 1, "region": 1, "district": 1, "market_name": 1},
        )
    }
    rows = []
    for a in assessments:
        t = traders.get(a.get("trader_id") or "", {})
        rows.append({
            "assessment_id": a.get("assessment_id", ""),
            "trader_name": t.get("name", ""),
            "business_name": a.get("business_name") or t.get("market_name") or "",
            "business_type": a.get("business_type") or t.get("business_type") or "",
            "tax_category": a.get("tax_category", ""),
            "period_label": a.get("period_label", ""),
            "amount_due": a.get("amount_due", 0),
            "amount_paid": a.get("amount_paid", 0),
            "status": a.get("status", ""),
            "due_date": a.get("due_date"),
            "region": a.get("region") or t.get("region") or "",
            "district": a.get("district") or t.get("district") or "",
        })
    return rows


def export_tax_payments_csv_rows(filters: dict) -> list[dict]:
    match: dict[str, Any] = {}
    if filters.get("status"):
        match["status"] = filters["status"]
    if filters.get("channel"):
        match["channel"] = filters["channel"]

    payments = list(
        get_collection(TAX_PAYMENTS)
        .find(match, {"_id": 0})
        .sort("created_at", -1)
        .limit(10000)
    )
    rows = []
    for p in payments:
        rows.append({
            "payment_id": p.get("payment_id", ""),
            "assessment_id": p.get("assessment_id", ""),
            "amount": p.get("amount_pesewas", p.get("amount", 0)),
            "channel": p.get("channel", ""),
            "momo_network": p.get("momo_network", ""),
            "provider": p.get("provider", ""),
            "status": p.get("status", ""),
            "created_at": p.get("created_at"),
        })
    return rows

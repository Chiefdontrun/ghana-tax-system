"""
Reports views:
  GET /api/reports/summary    — aggregated KPI summary
  GET /api/reports/export     — CSV download
  GET /api/traders            — paginated + filtered trader list
  GET /api/traders/<id>       — trader detail
"""

import logging

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.request import Request

from apps.auth_app.permissions import IsTaxAdmin
from apps.reports.serializers import (
    ReportsExportQuerySerializer,
    ReportsSummaryQuerySerializer,
    TradersListQuerySerializer,
)
from apps.reports.services import ReportsService
from core.utils.response import error_response, success_response, paginated_response

logger = logging.getLogger(__name__)

_service = ReportsService()


def _get_ip(request: Request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "unknown")


# ── Reports Summary ───────────────────────────────────────────────────────────

class ReportsSummaryView(APIView):
    """GET /api/reports/summary — TAX_ADMIN or SYS_ADMIN."""

    permission_classes = [IsTaxAdmin]

    def get(self, request: Request):
        qs = ReportsSummaryQuerySerializer(data=request.query_params)
        if not qs.is_valid():
            return error_response("Invalid query parameters.", errors=qs.errors)

        summary = _service.get_summary(
            period=qs.validated_data["period"],
            actor=request.admin,
        )
        return success_response(data=summary, message="Summary generated.")


# ── Reports Export ────────────────────────────────────────────────────────────

class ReportsExportView(APIView):
    """GET /api/reports/export — returns a CSV file download."""

    permission_classes = [IsTaxAdmin]

    def get(self, request: Request):
        qs = ReportsExportQuerySerializer(data=request.query_params)
        if not qs.is_valid():
            return error_response("Invalid query parameters.", errors=qs.errors)

        csv_content = _service.export_csv(
            validated_params=qs.validated_data,
            actor=request.admin,
            ip_address=_get_ip(request),
        )

        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="traders_export.csv"'
        return response


# ── Traders List ──────────────────────────────────────────────────────────────

class TradersListView(APIView):
    """GET /api/traders — paginated, filtered trader list."""

    permission_classes = [IsTaxAdmin]

    def get(self, request: Request):
        qs = TradersListQuerySerializer(data=request.query_params)
        if not qs.is_valid():
            return error_response("Invalid query parameters.", errors=qs.errors)

        result = _service.get_traders_list(qs.validated_data)
        return paginated_response(
            data=result["traders"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            message="Traders retrieved.",
        )


# ── Trader Detail ─────────────────────────────────────────────────────────────

class TraderDetailView(APIView):
    """GET /api/traders/<trader_id> — full trader profile."""

    permission_classes = [IsTaxAdmin]

    def get(self, request: Request, trader_id: str):
        trader = _service.get_trader_detail(trader_id)
        if not trader:
            return error_response("Trader not found.", http_status=404)
        return success_response(data=trader, message="Trader retrieved.")

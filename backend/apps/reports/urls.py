"""
Reports URL configuration — mounted at /api/reports/ in core/urls.py.
Trader list/detail also registered here and wired separately in core/urls.py.
"""

from django.urls import path
from apps.reports.views import (
    ReportsExportView,
    ReportsSummaryView,
    TradersListView,
    TraderDetailView,
)

# These are mounted at /api/reports/ via core/urls.py
reports_urlpatterns = [
    path("summary", ReportsSummaryView.as_view(), name="reports-summary"),
    path("export", ReportsExportView.as_view(), name="reports-export"),
]

# These are mounted at /api/traders/ via core/urls.py
traders_urlpatterns = [
    path("", TradersListView.as_view(), name="traders-list"),
    path("<str:trader_id>", TraderDetailView.as_view(), name="trader-detail"),
]

# Default urlpatterns for this module (reports prefix)
urlpatterns = reports_urlpatterns

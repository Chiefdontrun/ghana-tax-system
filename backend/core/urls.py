"""
Root URL configuration for ghana-tax-system backend.
"""

from django.urls import path, include
from apps.reports.urls import traders_urlpatterns

urlpatterns = [
    # Auth endpoints
    path("api/auth/", include("apps.auth_app.urls")),
    # Registration & TIN
    path("api/", include("apps.registration.urls")),
    path("api/tin/", include("apps.tin.urls")),
    # Reports + Traders
    path("api/reports/", include("apps.reports.urls")),
    path("api/traders/", include((traders_urlpatterns, "traders"))),
    # Audit logs + Admin user management
    path("api/audit-logs/", include("apps.audit.urls")),
    path("api/admin/", include("apps.auth_app.admin_urls")),
    path("api/tax/", include("apps.tax.urls")),
    # USSD webhook
    path("ussd/", include("apps.ussd.urls")),
]

"""Tax URL configuration."""

from django.urls import path
from apps.tax.views import TaxHealthView

urlpatterns = [
    path("health/", TaxHealthView.as_view(), name="tax-health"),
]

"""
TIN URL configuration — mounted at /api/tin/ in core/urls.py
"""

from django.urls import path
from apps.tin.views import TINLookupView

urlpatterns = [
    path("lookup", TINLookupView.as_view(), name="tin-lookup"),
]

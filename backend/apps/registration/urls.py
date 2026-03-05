"""
Registration URL configuration — mounted at /api/ in core/urls.py
"""

from django.urls import path
from apps.registration.views import RegisterTraderView

urlpatterns = [
    path("register", RegisterTraderView.as_view(), name="register-trader"),
]

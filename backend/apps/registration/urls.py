"""
Registration URL configuration — mounted at /api/ in core/urls.py
"""

from django.urls import path
from apps.registration.views import RegisterTraderView, MyBusinessesView

urlpatterns = [
    path("register/", RegisterTraderView.as_view(), name="register-trader"),
    path("my-businesses/", MyBusinessesView.as_view(), name="my-businesses"),
]

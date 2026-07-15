"""
USSD URL configuration — mounted at /ussd/ in core/urls.py
"""

from django.urls import path
from apps.ussd.views import USSDCallbackView
from apps.ussd.capture import ArkeselCaptureView

urlpatterns = [
    path("callback/", USSDCallbackView.as_view(), name="ussd-callback"),
    path("arkesel-capture/", ArkeselCaptureView.as_view(), name="ussd-arkesel-capture"),
]

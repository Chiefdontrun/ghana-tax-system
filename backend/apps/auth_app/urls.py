"""
auth_app URL configuration — /api/auth/...
"""

from django.urls import path
from apps.auth_app.views import LoginView, RefreshView, MeView, VerifyOtpView, ResendOtpView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("verify-otp/", VerifyOtpView.as_view(), name="auth-verify-otp"),
    path("resend-otp/", ResendOtpView.as_view(), name="auth-resend-otp"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]


from django.urls import path
from apps.trader_auth.views import TraderOtpRequestView, TraderOtpVerifyView, TraderRefreshView

urlpatterns = [
    path("request-otp/", TraderOtpRequestView.as_view(), name="trader-request-otp"),
    path("verify-otp/", TraderOtpVerifyView.as_view(), name="trader-verify-otp"),
    path("refresh/", TraderRefreshView.as_view(), name="trader-refresh"),
]

from django.urls import path
from apps.trader_auth.views import TraderOtpRequestView, TraderOtpVerifyView

urlpatterns = [
    path("request-otp/", TraderOtpRequestView.as_view(), name="trader-request-otp"),
    path("verify-otp/", TraderOtpVerifyView.as_view(), name="trader-verify-otp"),
]

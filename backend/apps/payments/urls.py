from django.urls import path
from apps.payments.views import (
    PaymentInitiateView, 
    PaymentStatusView,
    SubmitOtpView,
    PaystackWebhookView
)

urlpatterns = [
    path("initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("<str:payment_id>/status/", PaymentStatusView.as_view(), name="payment-status"),
    path("<str:payment_id>/submit-otp/", SubmitOtpView.as_view(), name="payment-submit-otp"),
    path("webhook/", PaystackWebhookView.as_view(), name="payment-webhook"),
]

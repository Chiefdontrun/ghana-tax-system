from django.urls import path
from apps.payments.views import (
    PaymentInitiateView,
    PaymentStatusView,
    SubmitOtpView,
    PaystackWebhookView,
    RunPendingPaymentCheckView,
)

urlpatterns = [
    path("initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    # Cron / external scheduler (must be before <payment_id> routes)
    path(
        "run-pending-check/",
        RunPendingPaymentCheckView.as_view(),
        name="payment-run-pending-check",
    ),
    path("<str:payment_id>/status/", PaymentStatusView.as_view(), name="payment-status"),
    path("<str:payment_id>/submit-otp/", SubmitOtpView.as_view(), name="payment-submit-otp"),
    path("webhook/", PaystackWebhookView.as_view(), name="payment-webhook"),
]

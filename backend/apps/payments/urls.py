from django.urls import path
from apps.payments.views import PaymentInitiateView, PaymentStatusView

urlpatterns = [
    path("initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("<str:payment_id>/status/", PaymentStatusView.as_view(), name="payment-status"),
]

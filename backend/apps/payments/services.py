import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def _build_provider():
    """Return the appropriate payment provider based on environment config."""
    if getattr(settings, "PAYSTACK_SECRET_KEY", ""):
        from apps.payments.providers.paystack import PaystackMoMoProvider
        logger.info("PaymentService: using PaystackMoMoProvider")
        return PaystackMoMoProvider()
    from apps.payments.providers.stub import StubPaymentProvider
    logger.info("PaymentService: using StubPaymentProvider (no Paystack credentials)")
    return StubPaymentProvider()

class PaymentService:
    """Thin wrapper around the active payment provider."""

    def __init__(self):
        self._provider = _build_provider()

    def initiate_charge(
        self,
        amount_pesewas: int,
        phone_number: str,
        momo_network: str,
        reference: str,
        callback_url: str = None
    ):
        return self._provider.initiate_charge(
            amount_pesewas=amount_pesewas,
            phone_number=phone_number,
            momo_network=momo_network,
            reference=reference,
            callback_url=callback_url
        )

    def verify_transaction(self, provider_reference: str):
        return self._provider.verify_transaction(provider_reference)

import logging
import uuid
from typing import Optional
from apps.payments.providers.base import PaymentProvider, ChargeResult, TransactionStatus

logger = logging.getLogger(__name__)


class StubPaymentProvider(PaymentProvider):
    """
    Fallback provider when Paystack API keys are not configured.
    Provides fake/synthetic responses without making any network calls.
    """

    def initiate_charge(
        self,
        amount_pesewas: int,
        phone_number: str,
        momo_network: str,
        reference: str,
        callback_url: Optional[str] = None
    ) -> ChargeResult:
        logger.info(
            "StubPaymentProvider: Initiating mock charge for %s pesewas "
            "to %s via %s (Ref: %s)",
            amount_pesewas, phone_number, momo_network, reference
        )
        
        return ChargeResult(
            status="PENDING_AUTHORIZATION",
            provider_reference=f"STUB_REF_{uuid.uuid4().hex[:8]}",
            raw_response={"mock": True, "message": "Stub response"}
        )

    def verify_transaction(self, provider_reference: str) -> TransactionStatus:
        logger.info(
            "StubPaymentProvider: Verifying mock transaction for reference %s",
            provider_reference
        )
        
        # Stub always returns SUCCESS for testing flow.
        return TransactionStatus(
            status="SUCCESS",
            provider_reference=provider_reference,
            raw_response={"mock": True, "message": "Stub response"}
        )

    def submit_otp(self, provider_reference: str, otp: str) -> ChargeResult:
        logger.info(f"StubPaymentProvider: Submitted OTP {otp} for reference {provider_reference}")
        return ChargeResult(
            status="SUCCESS",
            provider_reference=provider_reference,
            raw_response={"mock_otp_submission": True}
        )

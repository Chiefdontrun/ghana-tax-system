import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from django.conf import settings

from apps.payments.exceptions import PaymentInitiationError, PaymentNotFoundError
from apps.tax.repository import TaxAssessmentRepository, TaxPaymentRepository
from apps.audit.repository import AuditRepository

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

class PaymentProviderService:
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


class PaymentService:
    def __init__(self):
        self.assessment_repo = TaxAssessmentRepository()
        self.payment_repo = TaxPaymentRepository()
        self.audit_repo = AuditRepository()
        self.provider_svc = PaymentProviderService()

    def initiate_payment(
        self,
        assessment_id: str,
        momo_network: str,
        phone_number: str,
        channel: str,
        actor_trader_id: str,
        amount_pesewas: Optional[int] = None
    ) -> dict:
        momo_network = momo_network.lower()
        if momo_network not in {"mtn", "telecel", "airteltigo"}:
            raise PaymentInitiationError(f"Invalid momo_network: {momo_network}")

        assessment = self.assessment_repo.find_by_id(assessment_id)
        if not assessment or assessment.get("trader_id") != actor_trader_id:
            raise PaymentNotFoundError("Assessment not found.")

        # Check if already paid
        amount_due = assessment.get("amount_due", 0)
        amount_paid = assessment.get("amount_paid", 0)
        if assessment.get("status") == "PAID" or amount_due <= amount_paid:
            raise PaymentInitiationError("This assessment has already been paid in full.")

        remaining_balance = amount_due - amount_paid

        if amount_pesewas is not None:
            if amount_pesewas <= 0:
                raise PaymentInitiationError("Payment amount must be greater than zero.")
            if amount_pesewas > remaining_balance:
                raise PaymentInitiationError(f"Payment amount exceeds outstanding balance of {remaining_balance} pesewas.")
        else:
            amount_pesewas = remaining_balance

        # Idempotency / concurrent check
        existing_payments = self.payment_repo.find_by_assessment(assessment_id)
        now = datetime.now(timezone.utc)
        for ep in existing_payments:
            if ep.get("status") == "PENDING_AUTHORIZATION":
                created_at = ep.get("created_at")
                if created_at:
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    if now - created_at < timedelta(minutes=3):
                        return ep  # Return the existing pending payment to prevent duplicates

        payment_id = str(uuid.uuid4())
        
        # Initial row state
        payment_doc = {
            "payment_id": payment_id,
            "assessment_id": assessment_id,
            "trader_id": actor_trader_id,
            "amount_pesewas": amount_pesewas,
            "momo_network": momo_network,
            "phone_number": phone_number,
            "channel": channel,
            "status": "INITIATED",
            "provider_reference": None,
            "failure_reason": None,
        }
        self.payment_repo.create(payment_doc)

        # Provider invocation
        result = self.provider_svc.initiate_charge(
            amount_pesewas=amount_pesewas,
            phone_number=phone_number,
            momo_network=momo_network,
            reference=payment_id,
        )

        updates = {
            "status": result.status,
            "provider_reference": result.provider_reference,
        }
        if result.failure_reason:
            updates["failure_reason"] = result.failure_reason

        final_payment = self.payment_repo.update(payment_id, updates)

        self.audit_repo.log({
            "action": "PAYMENT_INITIATED" if result.status != "FAILED" else "PAYMENT_INITIATION_FAILED",
            "entity_type": "tax_payment",
            "entity_id": payment_id,
            "actor_type": "trader",
            "actor_id": actor_trader_id,
            "channel": channel,
            "details": {
                "assessment_id": assessment_id,
                "amount_pesewas": amount_pesewas,
                "status": result.status,
                "failure_reason": result.failure_reason,
            }
        })

        if result.status == "FAILED":
            raise PaymentInitiationError(result.failure_reason or "Payment charge failed.")

        return final_payment

    def get_payment_status(self, payment_id: str, actor_trader_id: str) -> dict:
        payment = self.payment_repo.find_by_id(payment_id)
        if not payment or payment.get("trader_id") != actor_trader_id:
            raise PaymentNotFoundError("Payment not found.")

        return {
            "payment_id": payment.get("payment_id"),
            "status": payment.get("status"),
            "amount_pesewas": payment.get("amount_pesewas"),
            "updated_at": payment.get("updated_at")
        }

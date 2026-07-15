import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from django.conf import settings

from apps.payments.exceptions import PaymentInitiationError, PaymentNotFoundError
from apps.tax.repository import TaxAssessmentRepository, TaxPaymentRepository
from apps.audit.repository import AuditRepository
from apps.notifications.services import NotificationService

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
        self.notification_svc = NotificationService()

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
            "provider_reference": payment_id, # we send payment_id as reference, set early for webhook race condition
            "failure_reason": None,
            "requires_otp": False,
            "display_text": None,
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
            "provider_reference": result.provider_reference or payment_id,
            "requires_otp": result.requires_otp,
            "display_text": result.display_text,
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
            "requires_otp": payment.get("requires_otp", False),
            "display_text": payment.get("display_text"),
            "updated_at": payment.get("updated_at")
        }

    def _finalize_successful_payment(self, payment_id: str, provider_reference: str) -> dict:
        """
        Internal method for finalizing a successful payment (idempotent).
        """
        payment = self.payment_repo.find_by_id(payment_id)
        if not payment:
            logger.error(f"Cannot finalize missing payment_id {payment_id}")
            return None
        
        # Idempotency guard
        if payment.get("status") == "SUCCESS":
            return payment
        
        # Update tax payment row
        self.payment_repo.update(payment_id, {"status": "SUCCESS"})
        
        # Update tax assessment
        assessment_id = payment["assessment_id"]
        assessment = self.assessment_repo.find_by_id(assessment_id)
        if assessment:
            amount_paid_so_far = assessment.get("amount_paid", 0)
            amount_due = assessment.get("amount_due", 0)
            payment_amount = payment.get("amount_pesewas", 0)
            
            new_amount_paid = amount_paid_so_far + payment_amount
            overpaid_excess = 0
            
            if new_amount_paid >= amount_due:
                overpaid_excess = new_amount_paid - amount_due
                new_amount_paid = amount_due
                new_status = "PAID"
            else:
                new_status = "PARTIAL"
            
            self.assessment_repo.update(assessment_id, {
                "amount_paid": new_amount_paid,
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            })
            
            # Send SMS receipt
            try:
                msg = f"Receipt: GHS {payment_amount/100:.2f} received for tax assessment {assessment_id}. Thank you."
                self.notification_svc.send_sms(payment.get("phone_number"), msg)
            except Exception as e:
                logger.error(f"Failed to send SMS receipt for {payment_id}: {e}")
            
            # Write success audit log
            self.audit_repo.log({
                "action": "PAYMENT_SUCCEEDED",
                "entity_type": "tax_payment",
                "entity_id": payment_id,
                "actor_type": "system",
                "actor_id": "system",
                "channel": payment.get("channel"),
                "details": {
                    "provider_reference": provider_reference,
                    "assessment_id": assessment_id,
                    "amount_pesewas": payment_amount,
                    "overpaid_excess_pesewas": overpaid_excess
                }
            })
            
        return self.payment_repo.find_by_id(payment_id)

    def _handle_failed_payment(self, payment_id: str, provider_reference: str, reason: str) -> dict:
        payment = self.payment_repo.find_by_id(payment_id)
        if not payment or payment.get("status") in ["SUCCESS", "FAILED"]:
            return payment
        
        self.payment_repo.update(payment_id, {
            "status": "FAILED",
            "failure_reason": reason
        })
        
        self.audit_repo.log({
            "action": "PAYMENT_FAILED",
            "entity_type": "tax_payment",
            "entity_id": payment_id,
            "actor_type": "system",
            "actor_id": "system",
            "channel": payment.get("channel"),
            "details": {
                "provider_reference": provider_reference,
                "failure_reason": reason
            }
        })
        return self.payment_repo.find_by_id(payment_id)

    def submit_otp(self, payment_id: str, trader_id: str, otp: str) -> dict:
        payment = self.payment_repo.find_by_id(payment_id)
        if not payment or payment.get("trader_id") != trader_id:
            raise PaymentNotFoundError("Payment not found.")
        
        if payment.get("status") != "PENDING_AUTHORIZATION" or not payment.get("requires_otp"):
            raise PaymentInitiationError("Payment does not require OTP submission at this time.")
        
        provider_reference = payment.get("provider_reference")
        if not provider_reference:
            raise PaymentInitiationError("Payment missing provider reference.")
            
        result = self.provider_svc._provider.submit_otp(provider_reference, otp)
        
        if result.status == "SUCCESS":
            return self._finalize_successful_payment(payment_id, result.provider_reference)
        elif result.status == "FAILED":
            return self._handle_failed_payment(payment_id, result.provider_reference, result.failure_reason)
        else:
            # Remains pending
            return payment

    def process_paystack_webhook(self, event: str, data: dict):
        provider_reference = data.get("reference")
        if not provider_reference:
            logger.warning("Paystack webhook missing reference")
            return
            
        payment = self.payment_repo.find_by_id(provider_reference)
        if not payment:
            logger.warning(f"Paystack webhook reference {provider_reference} not found")
            return
            
        if event == "charge.success":
            self._finalize_successful_payment(provider_reference, provider_reference)
        elif event == "charge.failed" or event == "charge.abandoned":
            reason = data.get("gateway_response") or data.get("message") or "Webhook reported failure"
            self._handle_failed_payment(provider_reference, provider_reference, reason)

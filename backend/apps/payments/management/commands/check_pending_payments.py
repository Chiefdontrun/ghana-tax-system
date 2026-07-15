import logging
from django.core.management.base import BaseCommand
from apps.tax.repository import TaxPaymentRepository
from apps.payments.services import PaymentService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Polls PENDING_AUTHORIZATION payments older than 5 minutes and verifies them.'

    def handle(self, *args, **options):
        payment_repo = TaxPaymentRepository()
        payment_service = PaymentService()

        pending_payments = payment_repo.find_pending_older_than(5)
        count = len(pending_payments)
        
        self.stdout.write(self.style.NOTICE(f"Found {count} pending payments older than 5 minutes."))

        for payment in pending_payments:
            payment_id = payment.get("payment_id")
            provider_reference = payment.get("provider_reference")
            
            if not provider_reference:
                self.stdout.write(self.style.WARNING(f"Skipping payment {payment_id} (no provider reference)"))
                continue
                
            try:
                # Re-verify against provider
                result = payment_service.provider_svc.verify_transaction(provider_reference)
                
                if result.status == "SUCCESS":
                    payment_service._finalize_successful_payment(payment_id, provider_reference)
                    self.stdout.write(self.style.SUCCESS(f"Payment {payment_id} verified and finalized as SUCCESS."))
                elif result.status == "FAILED":
                    reason = result.raw_response.get("message") if result.raw_response else "Failed via verification poller."
                    payment_service._handle_failed_payment(payment_id, provider_reference, reason)
                    self.stdout.write(self.style.ERROR(f"Payment {payment_id} verified and marked as FAILED."))
                else:
                    self.stdout.write(self.style.NOTICE(f"Payment {payment_id} remains PENDING_AUTHORIZATION."))
            except Exception as e:
                logger.error(f"Error checking pending payment {payment_id}: {e}")
                self.stdout.write(self.style.ERROR(f"Error checking pending payment {payment_id}: {e}"))

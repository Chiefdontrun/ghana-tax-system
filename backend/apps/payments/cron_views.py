"""
HTTP trigger for check_pending_payments (payment safety net).

Auth: Authorization: Bearer <CRON_SECRET> or X-Cron-Secret: <CRON_SECRET>
Wire via Vercel crons or external scheduler every 5 minutes.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class CheckPendingPaymentsCronView(View):
    def post(self, request):
        return self._run(request)

    def get(self, request):
        # Vercel cron uses GET by default
        return self._run(request)

    def _run(self, request):
        expected = getattr(settings, "CRON_SECRET", "") or ""
        if not expected:
            return JsonResponse(
                {"success": False, "message": "CRON_SECRET not configured."},
                status=503,
            )

        auth = request.headers.get("Authorization", "")
        header_secret = request.headers.get("X-Cron-Secret", "")
        bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if header_secret != expected and bearer != expected:
            return JsonResponse(
                {"success": False, "message": "Unauthorized."},
                status=401,
            )

        from apps.tax.repository import TaxPaymentRepository
        from apps.payments.services import PaymentService

        payment_repo = TaxPaymentRepository()
        payment_service = PaymentService()
        pending = payment_repo.find_pending_older_than(5)
        finalized = 0
        failed = 0
        still_pending = 0

        for payment in pending:
            payment_id = payment.get("payment_id")
            provider_reference = payment.get("provider_reference")
            if not provider_reference:
                continue
            try:
                result = payment_service.provider_svc.verify_transaction(provider_reference)
                if result.status == "SUCCESS":
                    payment_service._finalize_successful_payment(payment_id, provider_reference)
                    finalized += 1
                elif result.status == "FAILED":
                    reason = (
                        result.raw_response.get("message")
                        if result.raw_response
                        else "Failed via verification poller."
                    )
                    payment_service._handle_failed_payment(
                        payment_id, provider_reference, reason
                    )
                    failed += 1
                else:
                    still_pending += 1
            except Exception as exc:
                logger.exception("Cron check_pending failed for %s: %s", payment_id, exc)
                still_pending += 1

        return JsonResponse(
            {
                "success": True,
                "message": "Pending payments checked.",
                "data": {
                    "scanned": len(pending),
                    "finalized_success": finalized,
                    "finalized_failed": failed,
                    "still_pending": still_pending,
                },
            }
        )

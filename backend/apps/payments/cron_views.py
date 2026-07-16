"""
Legacy/alternate cron path: GET|POST /api/cron/check-pending-payments/

Shares PaymentService.run_pending_payment_check() with
POST /api/tax/payments/run-pending-check/ and manage.py check_pending_payments.

Vercel Hobby cron may only fire daily — prefer an external 5-minute scheduler
against /api/tax/payments/run-pending-check/ with X-Cron-Secret.
"""

from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.payments.services import PaymentService
from apps.payments.views import _cron_secret_authorized


@method_decorator(csrf_exempt, name="dispatch")
class CheckPendingPaymentsCronView(View):
    def post(self, request):
        return self._run(request)

    def get(self, request):
        # Vercel cron uses GET by default
        return self._run(request)

    def _run(self, request):
        if not getattr(settings, "CRON_SECRET", ""):
            return JsonResponse(
                {"success": False, "message": "CRON_SECRET not configured."},
                status=503,
            )
        if not _cron_secret_authorized(request):
            return JsonResponse(
                {"success": False, "message": "Unauthorized."},
                status=401,
            )

        summary = PaymentService().run_pending_payment_check(older_than_minutes=5)
        return JsonResponse(
            {
                "success": True,
                "message": "Pending payments checked.",
                "data": summary,
            }
        )

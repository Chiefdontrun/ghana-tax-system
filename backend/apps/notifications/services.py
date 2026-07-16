"""
NotificationService — SMS abstraction layer.

Provider priority (active):
  1. Arkesel (ARKESEL_SMS_API_KEY)  ← primary (USSD + SMS same vendor)
  2. StubSMSProvider                ← local / no credentials

BrevoSMSProvider remains in the codebase (providers/brevo.py) but is NOT
selected here — Ghana sender-ID registration blocked production use.
Africa's Talking is also unused on the active chain.

All callers go through this service; they never touch providers directly.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _build_provider():
    """Return the appropriate SMS provider based on environment config."""
    if getattr(settings, "ARKESEL_SMS_API_KEY", ""):
        from apps.notifications.providers.arkesel import ArkeselSMSProvider

        logger.info("NotificationService: using ArkeselSMSProvider")
        return ArkeselSMSProvider()

    from apps.notifications.providers.stub import StubSMSProvider

    logger.info("NotificationService: using StubSMSProvider (no ARKESEL_SMS_API_KEY)")
    return StubSMSProvider()


class NotificationService:
    """Thin service wrapper around the active SMS provider."""

    def __init__(self):
        self._provider = _build_provider()

    def send_sms(self, phone: str, message: str) -> dict:
        """
        Generic SMS send (payment receipts, etc.).
        Returns {success, message_id, error}.
        """
        result = self._provider.send_sms(phone, message)
        if not result.get("success"):
            logger.warning(
                "SMS failed for %s: %s",
                phone,
                result.get("error"),
            )
        return result

    def send_tin_sms(self, phone: str, tin: str, name: str) -> dict:
        """
        Send TIN confirmation SMS to a newly registered trader.
        Returns the provider result dict: {success, message_id, error}.
        """
        message = (
            f"Dear {name}, your TIN is {tin}. "
            "Keep this safe. - District Assembly Revenue Unit"
        )
        return self.send_sms(phone, message)

    def send_otp_sms(self, phone: str, otp_code: str) -> dict:
        """
        Send a 6-digit OTP verification code.
        Returns the provider result dict: {success, message_id, error}.
        """
        message = (
            f"Your District Assembly portal verification code is {otp_code}. "
            "It expires in 5 minutes. Do not share this code."
        )
        return self.send_sms(phone, message)

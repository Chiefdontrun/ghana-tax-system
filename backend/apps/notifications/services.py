"""
NotificationService — SMS abstraction layer.

Provider priority:
  1. Brevo (BREVO_API_KEY or BREVO_SMS_API_KEY)  ← preferred
  2. Arkesel (ARKESEL_SMS_API_KEY)               ← legacy
  3. Africa's Talking (AT_API_KEY + AT_USERNAME) ← legacy
  4. StubSMSProvider                             ← local / no credentials

All callers go through this service; they never touch providers directly.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _build_provider():
    """Return the appropriate SMS provider based on environment config."""
    brevo_key = getattr(settings, "BREVO_API_KEY", "") or getattr(
        settings, "BREVO_SMS_API_KEY", ""
    )
    if brevo_key:
        from apps.notifications.providers.brevo import BrevoSMSProvider

        logger.info("NotificationService: using BrevoSMSProvider")
        return BrevoSMSProvider()

    if getattr(settings, "ARKESEL_SMS_API_KEY", ""):
        from apps.notifications.providers.arkesel import ArkeselSMSProvider

        logger.info("NotificationService: using ArkeselSMSProvider (legacy)")
        return ArkeselSMSProvider()

    if getattr(settings, "AT_API_KEY", "") and getattr(settings, "AT_USERNAME", ""):
        from apps.notifications.providers.africas_talking import AfricasTalkingProvider

        logger.info("NotificationService: using AfricasTalkingProvider (legacy)")
        return AfricasTalkingProvider()

    from apps.notifications.providers.stub import StubSMSProvider

    logger.info("NotificationService: using StubSMSProvider (no credentials)")
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

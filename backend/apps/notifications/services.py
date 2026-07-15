"""
NotificationService — SMS abstraction layer.
Provider is selected at startup based on AT_API_KEY presence.
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
    if getattr(settings, "AT_API_KEY", "") and getattr(settings, "AT_USERNAME", ""):
        from apps.notifications.providers.africas_talking import AfricasTalkingProvider
        logger.info("NotificationService: using AfricasTalkingProvider")
        return AfricasTalkingProvider()
    from apps.notifications.providers.stub import StubSMSProvider
    logger.info("NotificationService: using StubSMSProvider (no credentials)")
    return StubSMSProvider()


class NotificationService:
    """Thin service wrapper around the active SMS provider."""

    def __init__(self):
        self._provider = _build_provider()

    def send_tin_sms(self, phone: str, tin: str, name: str) -> dict:
        """
        Send TIN confirmation SMS to a newly registered trader.
        Returns the provider result dict: {success, message_id, error}.
        """
        message = (
            f"Dear {name}, your TIN is {tin}. "
            "Keep this safe. - District Assembly Revenue Unit"
        )
        result = self._provider.send_sms(phone, message)
        if not result.get("success"):
            logger.warning(
                "TIN SMS failed for %s (%s): %s",
                phone, tin, result.get("error"),
            )
        return result

    def send_otp_sms(self, phone: str, otp_code: str) -> dict:
        """
        Send a 6-digit OTP verification code.
        Returns the provider result dict: {success, message_id, error}.
        """
        message = (
            f"Your District Assembly portal verification code is {otp_code}. "
            "It expires in 5 minutes. Do not share this code."
        )
        result = self._provider.send_sms(phone, message)
        if not result.get("success"):
            logger.warning(
                "OTP SMS failed for %s: %s",
                phone, result.get("error"),
            )
        return result

"""
Email helpers for admin authentication.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Raised when an authentication email cannot be sent."""


class AdminAuthEmailService:
    """Sends admin authentication email through Django's configured backend."""

    def send_otp(self, email: str, code: str) -> None:
        subject = "Your Ghana Tax System verification code"
        message = (
            f"Your Ghana Tax System admin verification code is {code}.\n\n"
            "It expires in 5 minutes. Do not share this code with anyone."
        )
        try:
            sent_count = send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.warning("Admin OTP email failed for %s: %s", email, exc)
            raise EmailDeliveryError("Could not send verification code. Please try again.") from exc

        if sent_count < 1:
            raise EmailDeliveryError("Could not send verification code. Please try again.")

"""
Email helpers for admin authentication.
"""

import logging

import resend
from resend import Emails
from resend.exceptions import ResendError
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Raised when an authentication email cannot be sent."""


def _get_resend_client() -> Emails:
    api_key = getattr(settings, "RESEND_API_KEY", "")
    if not api_key:
        raise EmailDeliveryError(
            "Email sending is not configured. Set RESEND_API_KEY in the environment."
        )

    resend.api_key = api_key
    return Emails()


class AdminAuthEmailService:
    """Sends admin authentication email through the Resend provider."""

    def send_otp(self, email: str, code: str) -> None:
        subject = "Your Ghana Tax System verification code"
        message = (
            f"Your Ghana Tax System admin verification code is {code}.\n\n"
            "It expires in 5 minutes. Do not share this code with anyone."
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")
        if not from_email:
            raise EmailDeliveryError(
                "Email sender is not configured. Set DEFAULT_FROM_EMAIL in the environment."
            )

        if "@ghana-tax.local" in from_email:
            raise EmailDeliveryError(
                "DEFAULT_FROM_EMAIL must be updated to a real verified sender address."
            )

        try:
            client = _get_resend_client()
            response = client.send(
                {
                    "from": from_email,
                    "to": email,
                    "subject": subject,
                    "text": message,
                }
            )
        except EmailDeliveryError:
            raise
        except ResendError as exc:
            logger.warning(
                "Admin OTP email failed for %s: %s",
                email,
                exc,
                exc_info=True,
            )
            raise EmailDeliveryError(
                "Could not send verification code. Please try again."
            ) from exc
        except Exception as exc:
            logger.warning(
                "Admin OTP email failed for %s: %s",
                email,
                exc,
                exc_info=True,
            )
            raise EmailDeliveryError(
                "Could not send verification code. Please try again."
            ) from exc

        if not getattr(response, "id", None):
            raise EmailDeliveryError(
                "Email provider did not confirm delivery of the verification code."
            )

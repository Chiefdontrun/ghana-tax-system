"""
AfricasTalkingProvider — real SMS via the Africa's Talking HTTP API.
Falls back to StubSMSProvider behaviour when AT_API_KEY is not configured.
"""

import logging

from django.conf import settings

from apps.notifications.providers.base import SMSProvider

logger = logging.getLogger(__name__)


class AfricasTalkingProvider(SMSProvider):
    """
    Sends SMS via Africa's Talking REST API.
    Requires AT_API_KEY and AT_USERNAME to be set in the environment.
    If either is missing, falls back to stub behaviour (logs only).
    """

    AT_API_URL = "https://api.africastalking.com/version1/messaging"

    def send_sms(self, phone: str, message: str) -> dict:
        api_key = getattr(settings, "AT_API_KEY", "")
        username = getattr(settings, "AT_USERNAME", "")
        sender_id = getattr(settings, "AT_SENDER_ID", "GH-REVENUE")

        # Fall back to stub if credentials are absent
        if not api_key or not username:
            logger.warning(
                "AT_API_KEY/AT_USERNAME not configured — falling back to stub SMS for %s",
                phone,
            )
            from apps.notifications.providers.stub import StubSMSProvider
            return StubSMSProvider().send_sms(phone, message)

        try:
            import urllib.request
            import urllib.parse
            import json

            payload = urllib.parse.urlencode({
                "username": username,
                "to": phone,
                "message": message,
                "from": sender_id,
            }).encode("utf-8")

            req = urllib.request.Request(
                self.AT_API_URL,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "apiKey": api_key,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            recipients = (
                body.get("SMSMessageData", {})
                    .get("Recipients", [])
            )
            if recipients and recipients[0].get("statusCode") == 101:
                message_id = recipients[0].get("messageId", "")
                logger.info("AT SMS sent to %s — id: %s", phone, message_id)
                return {"success": True, "message_id": message_id, "error": None}

            error_msg = recipients[0].get("status", "Unknown AT error") if recipients else "No recipients"
            logger.error("AT SMS failed for %s: %s", phone, error_msg)
            return {"success": False, "message_id": None, "error": error_msg}

        except Exception as exc:
            logger.exception("AT SMS exception for %s: %s", phone, exc)
            return {"success": False, "message_id": None, "error": str(exc)}

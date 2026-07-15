"""
Brevo (Sendinblue) transactional SMS provider.

Docs: POST https://api.brevo.com/v3/transactionalSMS/send
Auth header: api-key: <BREVO_API_KEY>
"""

from __future__ import annotations

import logging

import requests
from django.conf import settings

from apps.notifications.providers.base import SMSProvider

logger = logging.getLogger(__name__)

_BREVO_SMS_URL = "https://api.brevo.com/v3/transactionalSMS/send"


class BrevoSMSProvider(SMSProvider):
    """
    Brevo transactional SMS.
    Requires BREVO_API_KEY. Optional BREVO_SMS_SENDER (default GH-REVENUE).
    """

    def __init__(self):
        self.api_key = getattr(settings, "BREVO_API_KEY", "") or getattr(
            settings, "BREVO_SMS_API_KEY", ""
        )
        self.sender = getattr(settings, "BREVO_SMS_SENDER", "") or "GH-REVENUE"
        # Brevo sender IDs are typically alphanumeric, max 11 chars for alpha
        self.sender = str(self.sender)[:11]
        self.endpoint = _BREVO_SMS_URL

    def send_sms(self, phone: str, message: str) -> dict:
        if not self.api_key:
            return {
                "success": False,
                "message_id": None,
                "error": "Missing BREVO_API_KEY",
            }

        # Brevo expects international format without '+', e.g. 23324xxxxxxx
        recipient = (phone or "").strip().replace(" ", "").replace("-", "")
        if recipient.startswith("+"):
            recipient = recipient[1:]

        payload = {
            "sender": self.sender,
            "recipient": recipient,
            "content": message,
            "type": "transactional",
            "unicodeEnabled": True,
        }

        headers = {
            "api-key": self.api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=15,
            )
            # Brevo returns 201 on success for transactional SMS
            try:
                data = response.json()
            except ValueError:
                data = {}

            if response.status_code in (200, 201):
                # Typical: {"messageId": 123456, "smsCount": 1, ...}
                msg_id = data.get("messageId") or data.get("reference") or data.get("message_id")
                return {
                    "success": True,
                    "message_id": str(msg_id) if msg_id is not None else "brevo-ok",
                    "error": None,
                }

            err = (
                data.get("message")
                or data.get("error")
                or response.text
                or f"HTTP {response.status_code}"
            )
            logger.error("Brevo SMS failed for %s: %s", recipient, err)
            return {"success": False, "message_id": None, "error": str(err)}

        except requests.exceptions.RequestException as exc:
            logger.error("Brevo SMS connection failed: %s", exc)
            return {"success": False, "message_id": None, "error": str(exc)}

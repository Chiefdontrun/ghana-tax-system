"""
StubSMSProvider — logs intent without making any network call.
Used in development, testing, and when AT credentials are absent.
"""

import logging
from uuid import uuid4

from apps.notifications.providers.base import SMSProvider

logger = logging.getLogger(__name__)


class StubSMSProvider(SMSProvider):
    def send_sms(self, phone: str, message: str) -> dict:
        message_id = f"stub-{uuid4().hex[:8]}"
        logger.info("[SMS STUB] To: %s | Msg: %s | id: %s", phone, message, message_id)
        return {"success": True, "message_id": message_id, "error": None}

"""
SMSProvider — abstract base class for all SMS provider implementations.
"""

from abc import ABC, abstractmethod


class SMSProvider(ABC):
    """
    All concrete SMS providers must implement send_sms().
    Return shape is always:
      {success: bool, message_id: str | None, error: str | None}
    """

    @abstractmethod
    def send_sms(self, phone: str, message: str) -> dict:
        """
        Send an SMS message.

        Args:
            phone:   Normalised phone number (+233XXXXXXXXX)
            message: Plain-text message body

        Returns:
            {"success": bool, "message_id": str | None, "error": str | None}
        """

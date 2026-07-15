import logging
import requests
from django.conf import settings
from apps.notifications.providers.base import SMSProvider

logger = logging.getLogger(__name__)

class ArkeselSMSProvider(SMSProvider):
    """
    Arkesel v2 SMS Provider implementation.
    Docs: https://arkesel.com/api/sms/
    """
    def __init__(self):
        self.api_key = getattr(settings, "ARKESEL_SMS_API_KEY", "")
        self.sender_id = getattr(settings, "ARKESEL_SENDER_ID", "GH-REVENUE")
        self.endpoint = "https://sms.arkesel.com/api/v2/sms/send"

    def send_sms(self, phone: str, message: str) -> dict:
        if not self.api_key:
            return {"success": False, "message_id": None, "error": "Missing Arkesel API Key"}

        # Arkesel expects recipients without the '+' sign if possible, or standard international.
        # It's safest to strip '+' if it exists, though they often support both. Let's just pass it.
        # "Recipients can be an array of numbers like ['233XXXXXXXXX']"
        clean_phone = phone.replace("+", "")

        payload = {
            "sender": self.sender_id,
            "message": message,
            "recipients": [clean_phone]
        }

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Example response: {"status": "success", "data": [{"id": "xyz", ...}]}
            status = data.get("status")
            if status == "success":
                msg_id = None
                resp_data = data.get("data", [])
                if isinstance(resp_data, list) and len(resp_data) > 0:
                    msg_id = resp_data[0].get("id")
                
                return {"success": True, "message_id": str(msg_id) if msg_id else "unknown", "error": None}
            else:
                return {"success": False, "message_id": None, "error": data.get("message", "API Error")}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Arkesel API connection failed: {e}")
            return {"success": False, "message_id": None, "error": str(e)}


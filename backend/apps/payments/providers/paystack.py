import logging
from typing import Optional
import requests
from django.conf import settings
from apps.payments.providers.base import PaymentProvider, ChargeResult, TransactionStatus

logger = logging.getLogger(__name__)


class PaystackMoMoProvider(PaymentProvider):
    """
    Paystack implementation for Mobile Money charges.
    Interacts with the Paystack Charge API.
    """

    MOMO_NETWORK_MAP = {
        "mtn": "mtn",
        "telecel": "vod",
        "airteltigo": "atl",
    }

    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = settings.PAYSTACK_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initiate_charge(
        self,
        amount_pesewas: int,
        phone_number: str,
        momo_network: str,
        reference: str,
        callback_url: Optional[str] = None
    ) -> ChargeResult:
        
        provider_code = self.MOMO_NETWORK_MAP.get(momo_network.lower())
        if not provider_code:
            return ChargeResult(
                status="FAILED",
                provider_reference=None,
                failure_reason=f"Unsupported mobile money network: {momo_network}"
            )

        # We must synthesize an email since Paystack requires it, but we don't track it.
        # {trader_id}@noemail.ghanataxsystem.local is our standard placeholder.
        synthesized_email = f"trader_{phone_number}@noemail.ghanataxsystem.local"

        payload = {
            "email": synthesized_email,
            "amount": amount_pesewas,
            "currency": "GHS",
            "reference": reference,
            "mobile_money": {
                "phone": phone_number,
                "provider": provider_code,
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/charge",
                json=payload,
                headers=self.headers,
                timeout=15
            )
            raw_data = response.json()
        except requests.RequestException as e:
            logger.error("Paystack network failure during initiate_charge: %s", e)
            return ChargeResult(
                status="FAILED",
                provider_reference=None,
                failure_reason="Network failure communicating with payment provider."
            )
        except ValueError:
            logger.error("Paystack returned invalid JSON during initiate_charge: %s", response.text)
            return ChargeResult(
                status="FAILED",
                provider_reference=None,
                failure_reason="Invalid response from payment provider."
            )

        if not raw_data.get("status"):
            # Paystack returns status=False for validation errors or API failures
            return ChargeResult(
                status="FAILED",
                provider_reference=None,
                failure_reason=raw_data.get("message", "Unknown error from Paystack."),
                raw_response=raw_data
            )

        data = raw_data.get("data", {})
        paystack_status = data.get("status")
        provider_reference = data.get("reference")

        # In a MoMo charge, Paystack usually returns "pay_offline" or "send_otp" depending on network,
        # but the transaction itself has a status like "pending" or "pay_offline".
        # If it requires user to approve on their device (standard for MTN/Telecel):
        if paystack_status in ["pay_offline", "pending", "send_otp"]:
            return ChargeResult(
                status="PENDING_AUTHORIZATION",
                provider_reference=provider_reference,
                raw_response=raw_data
            )
        elif paystack_status == "success":
            return ChargeResult(
                status="SUCCESS",
                provider_reference=provider_reference,
                raw_response=raw_data
            )
        else:
            return ChargeResult(
                status="FAILED",
                provider_reference=provider_reference,
                failure_reason=data.get("message", "Transaction failed."),
                raw_response=raw_data
            )

    def verify_transaction(self, provider_reference: str) -> TransactionStatus:
        try:
            response = requests.get(
                f"{self.base_url}/transaction/verify/{provider_reference}",
                headers=self.headers,
                timeout=10
            )
            raw_data = response.json()
        except requests.RequestException as e:
            logger.error("Paystack network failure during verify_transaction: %s", e)
            return TransactionStatus(
                status="PENDING_AUTHORIZATION", # Keep pending if we can't reach them
                provider_reference=provider_reference,
            )
        except ValueError:
            logger.error("Paystack returned invalid JSON during verify_transaction")
            return TransactionStatus(
                status="PENDING_AUTHORIZATION",
                provider_reference=provider_reference,
            )

        if not raw_data.get("status"):
             return TransactionStatus(
                status="FAILED",
                provider_reference=provider_reference,
                raw_response=raw_data
            )
            
        data = raw_data.get("data", {})
        paystack_status = data.get("status")
        
        if paystack_status == "success":
            status = "SUCCESS"
        elif paystack_status in ["failed", "abandoned", "reversed"]:
            status = "FAILED"
        else:
            status = "PENDING_AUTHORIZATION"
            
        return TransactionStatus(
            status=status,
            provider_reference=provider_reference,
            raw_response=raw_data
        )

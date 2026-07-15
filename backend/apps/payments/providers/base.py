from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChargeResult:
    """
    Result of an initiation attempt.
    Status can be:
      - PENDING_AUTHORIZATION: Waiting for the user to approve on their device.
      - FAILED: Failed immediately due to insufficient funds, bad network, invalid phone, etc.
      - SUCCESS: Successfully authorized immediately (rare for MoMo).
    """
    status: str
    provider_reference: Optional[str] = None
    failure_reason: Optional[str] = None
    raw_response: Optional[dict] = None
    requires_otp: bool = False
    display_text: Optional[str] = None


@dataclass
class TransactionStatus:
    """
    Current status of a transaction in the provider.
    Status can be:
      - PENDING_AUTHORIZATION: Still waiting for user prompt.
      - FAILED: Failed/rejected by user or network.
      - SUCCESS: Paid successfully.
    """
    status: str
    provider_reference: str
    raw_response: Optional[dict] = None
    requires_otp: bool = False
    display_text: Optional[str] = None


class PaymentProvider(ABC):
    """
    Abstract base class for all payment provider implementations.
    """

    @abstractmethod
    def initiate_charge(
        self,
        amount_pesewas: int,
        phone_number: str,
        momo_network: str,
        reference: str,
        callback_url: Optional[str] = None
    ) -> ChargeResult:
        """
        Initiate a Mobile Money charge against the provider.
        
        Args:
            amount_pesewas: The amount to charge, in the smallest currency unit.
            phone_number: Normalized phone number.
            momo_network: One of ["mtn", "telecel", "airteltigo"].
            reference: Our internal unique transaction reference.
            callback_url: URL for webhooks/redirects (if applicable).
            
        Returns:
            ChargeResult representing the immediate outcome of the request.
        """
        pass

    @abstractmethod
    def verify_transaction(self, provider_reference: str) -> TransactionStatus:
        """
        Verify the final status of a transaction directly with the provider.
        
        Args:
            provider_reference: The provider's transaction ID (from ChargeResult).
            
        Returns:
            TransactionStatus indicating whether it succeeded, failed, or is still pending.
        """
        pass

    @abstractmethod
    def submit_otp(self, provider_reference: str, otp: str) -> ChargeResult:
        """
        Submit an OTP for a transaction that is in a requires_otp state.
        """
        pass

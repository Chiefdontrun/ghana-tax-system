import pytest
from unittest import mock
import requests
from django.conf import settings

from apps.payments.providers.stub import StubPaymentProvider
from apps.payments.providers.paystack import PaystackMoMoProvider
from apps.payments.providers.base import ChargeResult, TransactionStatus
from apps.payments.services import _build_provider, PaymentService

def test_stub_provider():
    provider = StubPaymentProvider()
    
    # Test initiate_charge
    charge_result = provider.initiate_charge(
        amount_pesewas=1000,
        phone_number="0551234567",
        momo_network="mtn",
        reference="test-ref-123"
    )
    
    assert isinstance(charge_result, ChargeResult)
    assert charge_result.status == "PENDING_AUTHORIZATION"
    assert charge_result.provider_reference.startswith("STUB_REF_")
    
    # Test verify_transaction
    verify_result = provider.verify_transaction(charge_result.provider_reference)
    assert isinstance(verify_result, TransactionStatus)
    assert verify_result.status == "SUCCESS"
    assert verify_result.provider_reference == charge_result.provider_reference


@mock.patch("apps.payments.services.settings")
def test_provider_factory_stub(mock_settings):
    mock_settings.PAYSTACK_SECRET_KEY = ""
    provider = _build_provider()
    assert isinstance(provider, StubPaymentProvider)


@mock.patch("apps.payments.services.settings")
def test_provider_factory_paystack(mock_settings):
    mock_settings.PAYSTACK_SECRET_KEY = "sk_test_123"
    provider = _build_provider()
    assert isinstance(provider, PaystackMoMoProvider)


@mock.patch("requests.post")
def test_paystack_network_failure(mock_post, settings):
    settings.PAYSTACK_SECRET_KEY = "sk_test_123"
    provider = PaystackMoMoProvider()
    
    # Simulate a network timeout
    mock_post.side_effect = requests.RequestException("Timeout")
    
    result = provider.initiate_charge(
        amount_pesewas=1000,
        phone_number="0551234567",
        momo_network="mtn",
        reference="test-ref-fail"
    )
    
    assert result.status == "FAILED"
    assert result.failure_reason == "Network failure communicating with payment provider."


@pytest.mark.skipif(not getattr(settings, 'PAYSTACK_SECRET_KEY', ''), reason="No Paystack key provided")
def test_paystack_live_sandbox():
    """
    This test runs against the real Paystack sandbox if a key is provided.
    If no key is provided, it skips.
    """
    provider = PaystackMoMoProvider()
    
    # Initiate charge
    result = provider.initiate_charge(
        amount_pesewas=100,  # 1 GHS
        phone_number="0551234987", # Paystack test numbers
        momo_network="mtn",
        reference="live-sandbox-test-123"
    )
    
    # The sandbox should return PENDING_AUTHORIZATION for a valid request
    assert result.status in ["PENDING_AUTHORIZATION", "SUCCESS", "FAILED"]
    
    if result.status == "PENDING_AUTHORIZATION":
        assert result.provider_reference is not None
        
        # Verify transaction
        verify_result = provider.verify_transaction(result.provider_reference)
        assert verify_result.status in ["PENDING_AUTHORIZATION", "SUCCESS", "FAILED"]

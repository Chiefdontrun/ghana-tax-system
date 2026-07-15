import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from unittest import mock
import pytest
from django.urls import reverse
from rest_framework import status
from django.conf import settings
from django.core.management import call_command

from apps.tax.repository import TaxAssessmentRepository, TaxPaymentRepository
from apps.audit.repository import AuditRepository
from apps.auth_app.jwt_utils import generate_access_token
from apps.payments.providers.base import TransactionStatus

@pytest.fixture
def assessment_repo():
    return TaxAssessmentRepository()

@pytest.fixture
def payment_repo():
    return TaxPaymentRepository()

@pytest.fixture
def audit_repo():
    return AuditRepository()

@pytest.fixture
def trader_headers(sample_trader):
    token = generate_access_token(sample_trader["trader_id"], "TRADER")
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

@pytest.fixture
def setup_c3_data(sample_trader, assessment_repo, payment_repo):
    trader_id = sample_trader["trader_id"]
    assessment = assessment_repo.create({
        "assessment_id": "assess_c3_123",
        "trader_id": trader_id,
        "amount_due": 10000,
        "amount_paid": 0,
        "status": "UNPAID"
    })
    
    payment = payment_repo.create({
        "payment_id": "pay_c3_456",
        "assessment_id": assessment["assessment_id"],
        "trader_id": trader_id,
        "amount_pesewas": 5000,
        "momo_network": "telecel",
        "phone_number": "0200000000",
        "channel": "web",
        "status": "PENDING_AUTHORIZATION",
        "provider_reference": "pay_c3_456",
        "failure_reason": None,
        "requires_otp": True,
        "display_text": "Enter OTP"
    })
    
    return {
        "trader_id": trader_id,
        "assessment_id": assessment["assessment_id"],
        "payment_id": payment["payment_id"]
    }

def sign_payload(payload_bytes, secret):
    return hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha512).hexdigest()

@pytest.mark.django_db
def test_webhook_signature_validation(client):
    url = reverse("payment-webhook")
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    
    payload = {"event": "charge.success", "data": {"reference": "fake_ref"}}
    payload_bytes = json.dumps(payload).encode('utf-8')
    
    # Missing signature -> 401
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Invalid signature -> 401
    response = client.post(url, payload, content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE="bad_sig")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Valid signature -> 200
    valid_sig = sign_payload(payload_bytes, "test_secret_key")
    response = client.post(url, payload, content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE=valid_sig)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_webhook_unknown_reference(client, payment_repo):
    url = reverse("payment-webhook")
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    
    payload = {"event": "charge.success", "data": {"reference": "unknown_ref"}}
    payload_bytes = json.dumps(payload).encode('utf-8')
    valid_sig = sign_payload(payload_bytes, "test_secret_key")
    
    # Should return 200 OK without exceptions
    response = client.post(url, payload, content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE=valid_sig)
    assert response.status_code == status.HTTP_200_OK
    assert payment_repo.find_by_id("unknown_ref") is None

@pytest.mark.django_db
def test_webhook_idempotency(client, setup_c3_data, assessment_repo, payment_repo, audit_repo):
    url = reverse("payment-webhook")
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    payment_id = setup_c3_data["payment_id"]
    assessment_id = setup_c3_data["assessment_id"]
    
    payload = {"event": "charge.success", "data": {"reference": payment_id}}
    payload_bytes = json.dumps(payload).encode('utf-8')
    valid_sig = sign_payload(payload_bytes, "test_secret_key")
    
    # First webhook -> updates status and amount_paid
    response1 = client.post(url, payload, content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE=valid_sig)
    assert response1.status_code == status.HTTP_200_OK
    
    assess1 = assessment_repo.find_by_id(assessment_id)
    assert assess1["amount_paid"] == 5000
    assert assess1["status"] == "PARTIAL"
    
    # Second webhook -> should be idempotent
    response2 = client.post(url, payload, content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE=valid_sig)
    assert response2.status_code == status.HTTP_200_OK
    
    assess2 = assessment_repo.find_by_id(assessment_id)
    assert assess2["amount_paid"] == 5000 # Still 5000
    
    logs = list(audit_repo._col().find({"entity_type": "tax_payment", "entity_id": payment_id, "action": "PAYMENT_SUCCEEDED"}))
    assert len(logs) == 1

@pytest.mark.django_db
def test_finalize_overpayment(client, setup_c3_data, assessment_repo, payment_repo, audit_repo):
    # Modify payment to exceed amount_due
    payment_id = setup_c3_data["payment_id"]
    assessment_id = setup_c3_data["assessment_id"]
    
    payment_repo.update(payment_id, {"amount_pesewas": 12000}) # due is 10000
    
    url = reverse("payment-webhook")
    settings.PAYSTACK_SECRET_KEY = "test_secret_key"
    
    payload = {"event": "charge.success", "data": {"reference": payment_id}}
    payload_bytes = json.dumps(payload).encode('utf-8')
    valid_sig = sign_payload(payload_bytes, "test_secret_key")
    
    client.post(url, payload, content_type="application/json", HTTP_X_PAYSTACK_SIGNATURE=valid_sig)
    
    assess = assessment_repo.find_by_id(assessment_id)
    assert assess["amount_paid"] == 10000 # Capped
    assert assess["status"] == "PAID"
    
    logs = list(audit_repo._col().find({"entity_type": "tax_payment", "entity_id": payment_id, "action": "PAYMENT_SUCCEEDED"}))
    assert logs[0]["details"]["overpaid_excess_pesewas"] == 2000

@pytest.mark.django_db
@mock.patch("apps.payments.services._build_provider")
def test_submit_otp_happy_path(mock_build, client, trader_headers, setup_c3_data, assessment_repo, payment_repo):
    from apps.payments.providers.stub import StubPaymentProvider
    mock_build.return_value = StubPaymentProvider()
    
    payment_id = setup_c3_data["payment_id"]
    url = reverse("payment-submit-otp", kwargs={"payment_id": payment_id})
    
    response = client.post(url, {"otp": "123456"}, **trader_headers)
    assert response.status_code == status.HTTP_200_OK
    
    payment = payment_repo.find_by_id(payment_id)
    assert payment["status"] == "SUCCESS"
    
    assess = assessment_repo.find_by_id(setup_c3_data["assessment_id"])
    assert assess["amount_paid"] == 5000

@pytest.mark.django_db
def test_submit_otp_rejected_if_not_required(client, trader_headers, setup_c3_data, payment_repo):
    payment_id = setup_c3_data["payment_id"]
    # Change requires_otp to False
    payment_repo.update(payment_id, {"requires_otp": False})
    
    url = reverse("payment-submit-otp", kwargs={"payment_id": payment_id})
    
    response = client.post(url, {"otp": "123456"}, **trader_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not require OTP" in response.data["error"]

@pytest.mark.django_db
@mock.patch("apps.payments.services.PaymentProviderService.verify_transaction")
def test_fallback_poller(mock_verify, setup_c3_data, payment_repo):
    payment_id_aged = setup_c3_data["payment_id"]
    
    # Make the existing payment 10 minutes old
    ten_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
    payment_repo._col().update_one({"payment_id": payment_id_aged}, {"$set": {"created_at": ten_mins_ago}})
    
    # Create a fresh pending payment (not aged)
    fresh_payment = payment_repo.create({
        "payment_id": "pay_fresh",
        "assessment_id": setup_c3_data["assessment_id"],
        "trader_id": setup_c3_data["trader_id"],
        "amount_pesewas": 1000,
        "momo_network": "mtn",
        "phone_number": "0550000000",
        "channel": "web",
        "status": "PENDING_AUTHORIZATION",
        "provider_reference": "pay_fresh"
    })
    
    # Mock verify to return SUCCESS for the aged one
    mock_verify.return_value = TransactionStatus(status="SUCCESS", provider_reference=payment_id_aged)
    
    # Run the poller
    from apps.payments.management.commands.check_pending_payments import Command
    Command().handle()
    
    # Aged should be SUCCESS
    assert payment_repo.find_by_id(payment_id_aged)["status"] == "SUCCESS"
    
    # Fresh should still be PENDING_AUTHORIZATION
    assert payment_repo.find_by_id("pay_fresh")["status"] == "PENDING_AUTHORIZATION"
    
    # Verify was only called once
    mock_verify.assert_called_once_with(payment_id_aged)

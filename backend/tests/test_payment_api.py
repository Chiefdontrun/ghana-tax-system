import pytest
from unittest import mock
from django.urls import reverse
from rest_framework import status
from datetime import datetime, timezone, timedelta

from apps.tax.repository import TaxAssessmentRepository, TaxPaymentRepository
from apps.audit.repository import AuditRepository
from apps.payments.providers.base import ChargeResult

from apps.auth_app.jwt_utils import generate_access_token

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
def setup_data(sample_trader, assessment_repo):
    assessment_id = "test_assessment_123"
    assessment = assessment_repo.create({
        "assessment_id": assessment_id,
        "trader_id": sample_trader["trader_id"],
        "amount_due": 5000,
        "amount_paid": 0,
        "status": "UNPAID"
    })
    return {
        "trader_id": sample_trader["trader_id"],
        "phone_number": sample_trader["phone_number"],
        "assessment_id": assessment_id
    }

@pytest.mark.django_db
@mock.patch("apps.payments.services._build_provider")
def test_initiate_payment_success(mock_build_provider, client, trader_headers, setup_data, payment_repo, audit_repo):
    from apps.payments.providers.stub import StubPaymentProvider
    mock_build_provider.return_value = StubPaymentProvider()

    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "amount_pesewas": 2000,
        "momo_network": "mtn"
    }

    # Use the stub provider which returns PENDING_AUTHORIZATION
    response = client.post(url, payload, content_type="application/json", **trader_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert "payment_id" in data
    assert data["status"] == "PENDING_AUTHORIZATION"
    assert data["amount_pesewas"] == 2000

    payment = payment_repo.find_by_id(data["payment_id"])
    assert payment is not None
    assert payment["status"] == "PENDING_AUTHORIZATION"
    assert payment["trader_id"] == setup_data["trader_id"]

    logs = list(audit_repo._col().find({"entity_type": "tax_payment", "entity_id": data["payment_id"]}))
    assert len(logs) == 1
    assert logs[0]["action"] == "PAYMENT_INITIATED"

@pytest.mark.django_db
def test_initiate_payment_ownership(client, trader_headers, assessment_repo):
    # Assessment belongs to some other trader
    other_assessment = assessment_repo.create({
        "assessment_id": "other_assess_123",
        "trader_id": "other_trader_123",
        "amount_due": 5000,
        "amount_paid": 0,
        "status": "UNPAID"
    })

    url = reverse("payment-initiate")
    payload = {
        "assessment_id": other_assessment["assessment_id"],
        "momo_network": "mtn"
    }

    response = client.post(url, payload, **trader_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["error"].lower()

@pytest.mark.django_db
@mock.patch("apps.payments.services._build_provider")
def test_initiate_payment_idempotency(mock_build_provider, client, trader_headers, setup_data, payment_repo):
    from apps.payments.providers.stub import StubPaymentProvider
    mock_build_provider.return_value = StubPaymentProvider()

    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "amount_pesewas": 2000,
        "momo_network": "mtn"
    }

    response1 = client.post(url, payload, content_type="application/json", **trader_headers)
    assert response1.status_code == status.HTTP_201_CREATED
    payment_id_1 = response1.json()["payment_id"]

    # Second call immediately after
    response2 = client.post(url, payload, **trader_headers)
    assert response2.status_code == status.HTTP_201_CREATED
    payment_id_2 = response2.json()["payment_id"]

    # Should return the exact same payment record
    assert payment_id_1 == payment_id_2

@pytest.mark.django_db
@mock.patch("apps.payments.services.PaymentProviderService.initiate_charge")
def test_already_paid_assessment(mock_charge, client, trader_headers, setup_data, assessment_repo):
    # Set amount_paid to amount_due
    assessment_repo._col().update_one(
        {"assessment_id": setup_data["assessment_id"]},
        {"$set": {"amount_paid": 5000, "status": "PAID"}}
    )

    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "momo_network": "mtn"
    }

    response = client.post(url, payload, **trader_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "paid in full" in response.json()["error"].lower()
    
    # Assert provider was never called
    mock_charge.assert_not_called()

@pytest.mark.django_db
def test_overpayment_rejected(client, trader_headers, setup_data):
    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "amount_pesewas": 6000,  # Owed is 5000
        "momo_network": "mtn"
    }

    response = client.post(url, payload, **trader_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds outstanding balance" in response.json()["error"].lower()

@pytest.mark.django_db
def test_invalid_momo_network(client, trader_headers, setup_data):
    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "momo_network": "invalid_net"
    }

    response = client.post(url, payload, **trader_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "momo_network" in response.json()

@pytest.mark.django_db
@mock.patch("apps.payments.services.PaymentProviderService.initiate_charge")
def test_provider_failed(mock_charge, client, trader_headers, setup_data, payment_repo, audit_repo):
    mock_charge.return_value = ChargeResult(
        status="FAILED",
        provider_reference=None,
        failure_reason="Insufficient funds"
    )

    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "momo_network": "mtn"
    }

    response = client.post(url, payload, **trader_headers)
    print(response.json())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Insufficient funds"

    # Verify DB recorded failure
    payments = payment_repo.find_by_assessment(setup_data["assessment_id"])
    assert payments[0]["status"] == "FAILED"
    assert payments[0]["failure_reason"] == "Insufficient funds"

    # Verify audit log
    logs = list(audit_repo._col().find({"entity_type": "tax_payment", "entity_id": payments[0]["payment_id"]}))
    assert logs[0]["action"] == "PAYMENT_INITIATION_FAILED"

@pytest.mark.django_db
def test_payment_status_endpoint(client, trader_headers, setup_data, payment_repo):
    payment_data = payment_repo.create({
        "payment_id": "test_pay_status",
        "assessment_id": setup_data["assessment_id"],
        "trader_id": setup_data["trader_id"],
        "amount_pesewas": 1000,
        "momo_network": "mtn",
        "phone_number": setup_data["phone_number"],
        "channel": "web",
        "status": "PENDING_AUTHORIZATION",
        "provider_reference": "ref-123",
        "failure_reason": None,
    })

    url = reverse("payment-status", args=[payment_data["payment_id"]])
    response = client.get(url, **trader_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["payment_id"] == "test_pay_status"
    assert data["status"] == "PENDING_AUTHORIZATION"
    assert data["amount_pesewas"] == 1000

@pytest.mark.django_db
def test_payment_status_ownership(client, trader_headers, payment_repo):
    # Payment belonging to someone else
    payment_data = payment_repo.create({
        "payment_id": "other_test_pay",
        "assessment_id": "other_assess_123",
        "trader_id": "other_trader_123",
        "amount_pesewas": 1000,
        "momo_network": "mtn",
        "phone_number": "0550000000",
        "channel": "web",
        "status": "PENDING_AUTHORIZATION",
        "provider_reference": "ref-123",
        "failure_reason": None,
    })

    url = reverse("payment-status", args=[payment_data["payment_id"]])
    response = client.get(url, **trader_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

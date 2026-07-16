"""Tests for run_pending_payment_check service + HTTP cron endpoint."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import uuid

import pytest
from django.test import override_settings


def _pending_payment(test_db, **kwargs):
    pid = str(uuid.uuid4())
    doc = {
        "payment_id": pid,
        "assessment_id": kwargs.get("assessment_id", str(uuid.uuid4())),
        "trader_id": kwargs.get("trader_id", str(uuid.uuid4())),
        "amount_pesewas": 1000,
        "status": "PENDING_AUTHORIZATION",
        "provider_reference": kwargs.get("provider_reference", f"ref-{pid[:8]}"),
        "channel": "web",
        "phone_number": "+233241111111",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=10),
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=10),
    }
    test_db["tax_payments"].insert_one(doc)
    return doc


@pytest.mark.django_db
def test_run_pending_payment_check_summary_shape(test_db):
    from apps.payments.services import PaymentService
    from apps.payments.providers.base import ChargeResult

    _pending_payment(test_db, provider_reference="ok-ref")
    _pending_payment(test_db, provider_reference="")  # skipped

    svc = PaymentService()
    mock_result = ChargeResult(
        status="SUCCESS",
        provider_reference="ok-ref",
        requires_otp=False,
        display_text=None,
        raw_response={},
    )
    with patch.object(svc.provider_svc, "verify_transaction", return_value=mock_result):
        # Avoid full finalize side effects (assessment may be missing)
        with patch.object(svc, "_finalize_successful_payment", return_value={}):
            summary = svc.run_pending_payment_check(older_than_minutes=5)

    assert summary["checked"] == 2
    assert summary["resolved_success"] == 1
    assert summary["skipped_no_reference"] == 1
    assert "resolved_failed" in summary
    assert "still_pending" in summary
    assert summary["older_than_minutes"] == 5


@pytest.mark.django_db
@override_settings(CRON_SECRET="test-cron-secret-value-not-for-prod")
def test_run_pending_check_endpoint_valid_secret(client):
    with patch(
        "apps.payments.views.PaymentService.run_pending_payment_check",
        return_value={
            "checked": 0,
            "resolved_success": 0,
            "resolved_failed": 0,
            "still_pending": 0,
            "skipped_no_reference": 0,
            "older_than_minutes": 5,
        },
    ) as mock_run:
        resp = client.post(
            "/api/tax/payments/run-pending-check/",
            HTTP_X_CRON_SECRET="test-cron-secret-value-not-for-prod",
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["checked"] == 0
    mock_run.assert_called_once()


@pytest.mark.django_db
@override_settings(CRON_SECRET="test-cron-secret-value-not-for-prod")
def test_run_pending_check_endpoint_missing_secret_401(client):
    with patch(
        "apps.payments.views.PaymentService.run_pending_payment_check"
    ) as mock_run:
        resp = client.post("/api/tax/payments/run-pending-check/")
    assert resp.status_code == 401
    mock_run.assert_not_called()


@pytest.mark.django_db
@override_settings(CRON_SECRET="test-cron-secret-value-not-for-prod")
def test_run_pending_check_endpoint_invalid_secret_401(client):
    with patch(
        "apps.payments.views.PaymentService.run_pending_payment_check"
    ) as mock_run:
        resp = client.post(
            "/api/tax/payments/run-pending-check/",
            HTTP_X_CRON_SECRET="wrong-secret",
        )
    assert resp.status_code == 401
    mock_run.assert_not_called()


@pytest.mark.django_db
@override_settings(CRON_SECRET="")
def test_run_pending_check_endpoint_secret_not_configured_503(client):
    resp = client.post(
        "/api/tax/payments/run-pending-check/",
        HTTP_X_CRON_SECRET="anything",
    )
    assert resp.status_code == 503

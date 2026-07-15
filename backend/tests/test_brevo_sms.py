"""Unit tests for Brevo SMS provider selection and payload shape."""

from unittest.mock import MagicMock, patch

import pytest


def test_build_provider_prefers_brevo(settings):
    settings.BREVO_API_KEY = "xkeysib-test"
    settings.BREVO_SMS_API_KEY = ""
    settings.ARKESEL_SMS_API_KEY = "arkesel-should-not-win"
    settings.AT_API_KEY = ""
    settings.AT_USERNAME = ""

    from apps.notifications.services import _build_provider
    from apps.notifications.providers.brevo import BrevoSMSProvider

    provider = _build_provider()
    assert isinstance(provider, BrevoSMSProvider)


def test_build_provider_brevo_sms_alias(settings):
    settings.BREVO_API_KEY = ""
    settings.BREVO_SMS_API_KEY = "xkeysib-alias"
    settings.ARKESEL_SMS_API_KEY = ""
    settings.AT_API_KEY = ""
    settings.AT_USERNAME = ""

    from apps.notifications.services import _build_provider
    from apps.notifications.providers.brevo import BrevoSMSProvider

    assert isinstance(_build_provider(), BrevoSMSProvider)


def test_build_provider_stub_when_no_keys(settings):
    settings.BREVO_API_KEY = ""
    settings.BREVO_SMS_API_KEY = ""
    settings.ARKESEL_SMS_API_KEY = ""
    settings.AT_API_KEY = ""
    settings.AT_USERNAME = ""

    from apps.notifications.services import _build_provider
    from apps.notifications.providers.stub import StubSMSProvider

    assert isinstance(_build_provider(), StubSMSProvider)


@patch("apps.notifications.providers.brevo.requests.post")
def test_brevo_send_sms_success(mock_post, settings):
    settings.BREVO_API_KEY = "xkeysib-test"
    settings.BREVO_SMS_SENDER = "GH-REVENUE"

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"messageId": 987654, "smsCount": 1}
    mock_post.return_value = mock_resp

    from apps.notifications.providers.brevo import BrevoSMSProvider

    result = BrevoSMSProvider().send_sms("+233241234567", "Hello trader")
    assert result["success"] is True
    assert result["message_id"] == "987654"

    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.brevo.com/v3/transactionalSMS/send"
    assert kwargs["headers"]["api-key"] == "xkeysib-test"
    assert kwargs["json"]["recipient"] == "233241234567"
    assert kwargs["json"]["sender"] == "GH-REVENUE"
    assert kwargs["json"]["content"] == "Hello trader"
    assert kwargs["json"]["type"] == "transactional"


@patch("apps.notifications.providers.brevo.requests.post")
def test_brevo_send_sms_api_error(mock_post, settings):
    settings.BREVO_API_KEY = "xkeysib-test"
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"message": "Invalid sender"}
    mock_resp.text = "Invalid sender"
    mock_post.return_value = mock_resp

    from apps.notifications.providers.brevo import BrevoSMSProvider

    result = BrevoSMSProvider().send_sms("233241234567", "Hi")
    assert result["success"] is False
    assert "Invalid" in (result["error"] or "")


def test_notification_service_send_sms_method(settings):
    settings.BREVO_API_KEY = ""
    settings.BREVO_SMS_API_KEY = ""
    settings.ARKESEL_SMS_API_KEY = ""
    settings.AT_API_KEY = ""
    settings.AT_USERNAME = ""

    from apps.notifications.services import NotificationService

    svc = NotificationService()
    out = svc.send_sms("+233200000000", "receipt test")
    assert out["success"] is True
    assert out["message_id"]

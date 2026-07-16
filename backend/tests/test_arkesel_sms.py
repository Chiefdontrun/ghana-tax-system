"""Unit tests for Arkesel SMS provider selection and payload shape."""

from unittest.mock import MagicMock, patch


def test_build_provider_prefers_arkesel(settings):
    settings.ARKESEL_SMS_API_KEY = "arkesel-test-key"
    settings.BREVO_API_KEY = "xkeysib-should-not-win"
    settings.BREVO_SMS_API_KEY = "xkeysib-should-not-win"
    settings.AT_API_KEY = "at-should-not-win"
    settings.AT_USERNAME = "sandbox"

    from apps.notifications.services import _build_provider
    from apps.notifications.providers.arkesel import ArkeselSMSProvider

    assert isinstance(_build_provider(), ArkeselSMSProvider)


def test_build_provider_ignores_brevo_when_arkesel_missing(settings):
    """Brevo key alone must NOT activate SMS (Brevo removed from selection path)."""
    settings.ARKESEL_SMS_API_KEY = ""
    settings.BREVO_API_KEY = "xkeysib-test"
    settings.BREVO_SMS_API_KEY = "xkeysib-test"
    settings.AT_API_KEY = "at-key"
    settings.AT_USERNAME = "sandbox"

    from apps.notifications.services import _build_provider
    from apps.notifications.providers.stub import StubSMSProvider

    assert isinstance(_build_provider(), StubSMSProvider)


def test_build_provider_stub_when_no_arkesel_key(settings):
    settings.ARKESEL_SMS_API_KEY = ""
    settings.BREVO_API_KEY = ""
    settings.BREVO_SMS_API_KEY = ""
    settings.AT_API_KEY = ""
    settings.AT_USERNAME = ""

    from apps.notifications.services import _build_provider
    from apps.notifications.providers.stub import StubSMSProvider

    assert isinstance(_build_provider(), StubSMSProvider)


@patch("apps.notifications.providers.arkesel.requests.post")
def test_arkesel_send_sms_success(mock_post, settings):
    settings.ARKESEL_SMS_API_KEY = "arkesel-test-key"
    settings.ARKESEL_SENDER_ID = "GH-REVENUE"

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "status": "success",
        "data": [{"id": "ark-msg-99"}],
    }
    mock_post.return_value = mock_resp

    from apps.notifications.providers.arkesel import ArkeselSMSProvider

    result = ArkeselSMSProvider().send_sms("+233241234567", "Hello trader")
    assert result["success"] is True
    assert result["message_id"] == "ark-msg-99"

    args, kwargs = mock_post.call_args
    assert args[0] == "https://sms.arkesel.com/api/v2/sms/send"
    assert kwargs["headers"]["api-key"] == "arkesel-test-key"
    assert kwargs["json"]["sender"] == "GH-REVENUE"
    assert kwargs["json"]["recipients"] == ["233241234567"]
    assert kwargs["json"]["message"] == "Hello trader"


@patch("apps.notifications.providers.arkesel.requests.post")
def test_arkesel_send_sms_api_error(mock_post, settings):
    settings.ARKESEL_SMS_API_KEY = "arkesel-test-key"
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"status": "error", "message": "Invalid sender"}
    mock_post.return_value = mock_resp

    from apps.notifications.providers.arkesel import ArkeselSMSProvider

    result = ArkeselSMSProvider().send_sms("233241234567", "Hi")
    assert result["success"] is False
    assert "Invalid" in (result["error"] or "")


def test_arkesel_missing_key(settings):
    settings.ARKESEL_SMS_API_KEY = ""
    from apps.notifications.providers.arkesel import ArkeselSMSProvider

    result = ArkeselSMSProvider().send_sms("+233200000000", "x")
    assert result["success"] is False
    assert "Missing" in (result["error"] or "")

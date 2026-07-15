"""
Arkesel USSD gateway adapter tests.

Fixtures are verbatim live captures from shortcode *928*309# (2026-07-15).
Confirmed: Possibility A — userData does NOT accumulate; newSession is the
only reliable first-dial signal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.ussd.views import adapt_gateway_input

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "arkesel_live_session.json"


def _live_fixtures() -> dict:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Adapter unit tests (no DB) ────────────────────────────────────────────────

def test_adapt_arkesel_initial_dial_clears_shortcode_userData():
    """newSession=true + userData='*928*309#' must become empty initial input."""
    fx = _live_fixtures()["request_1_initial_dial"]
    adapted = adapt_gateway_input(fx)

    assert adapted["is_arkesel"] is True
    assert adapted["input_mode"] == "arkesel"
    assert adapted["new_session"] is True
    assert adapted["session_id"] == "17841474871496131"
    assert adapted["msisdn"] == "233231804643"
    assert adapted["text"] == ""  # shortcode must NOT be parsed as menu input


def test_adapt_arkesel_follow_up_uses_userData_directly():
    """newSession=false + userData='1' must pass through as single-step input."""
    fx = _live_fixtures()["request_2_follow_up"]
    adapted = adapt_gateway_input(fx)

    assert adapted["is_arkesel"] is True
    assert adapted["input_mode"] == "arkesel"
    assert adapted["new_session"] is False
    assert adapted["session_id"] == "17841474871496131"
    assert adapted["text"] == "1"
    # Must NOT treat as history: no * split required or applied at adapter layer
    assert "*" not in adapted["text"]


def test_adapt_africas_talking_preserves_history_text():
    data = {
        "sessionId": "at-sess-1",
        "phoneNumber": "+233201000099",
        "text": "1*Kofi Mensah",
    }
    adapted = adapt_gateway_input(data)
    assert adapted["is_arkesel"] is False
    assert adapted["input_mode"] == "africas_talking"
    assert adapted["text"] == "1*Kofi Mensah"


def test_parse_input_arkesel_does_not_split_stars():
    """If a step value ever contained '*', Arkesel mode must not take last segment only."""
    from apps.ussd.state_machine import USSDStateMachine

    user_input, is_initial = USSDStateMachine._parse_input("ab*cd", "arkesel")
    assert user_input == "ab*cd"
    assert is_initial is False

    user_input, is_initial = USSDStateMachine._parse_input("", "arkesel")
    assert user_input == ""
    assert is_initial is True


def test_parse_input_at_uses_last_segment():
    from apps.ussd.state_machine import USSDStateMachine

    user_input, is_initial = USSDStateMachine._parse_input("1*Kofi*2", "africas_talking")
    assert user_input == "2"
    assert is_initial is False


# ── Live-fixture endpoint regression (needs Mongo/Redis via conftest) ─────────

@pytest.mark.django_db
def test_arkesel_live_fixture_full_session_sequence(client):
    """
    Replay the exact captured request pair through /ussd/callback/.

    Expected:
      Req1 (newSession, userData=*928*309#) → main menu, continueSession true
      Req2 (userData=1) → Register name prompt, continueSession true
    """
    fx = _live_fixtures()
    req1 = fx["request_1_initial_dial"]
    req2 = fx["request_2_follow_up"]

    # Use unique session id per test run so store state never collides
    sid = "test-live-" + req1["sessionID"]
    p1 = {**req1, "sessionID": sid}
    p2 = {**req2, "sessionID": sid}

    r1 = client.post(
        "/ussd/callback/",
        data=json.dumps(p1),
        content_type="application/json",
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["sessionID"] == sid
    assert d1["userID"] == "3NV5OX7PZK_HICOs"
    assert d1["msisdn"] == "233231804643"
    assert d1["continueSession"] is True
    assert "Register Business" in d1["message"]
    # Critical: first dial must NOT show "Invalid option" from parsing 309#
    assert "Invalid" not in d1["message"]

    r2 = client.post(
        "/ussd/callback/",
        data=json.dumps(p2),
        content_type="application/json",
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["continueSession"] is True
    assert "full name" in d2["message"].lower()


@pytest.mark.django_db
def test_arkesel_initial_dial_legacy_name(client):
    """Back-compat name used by earlier Phase E tests."""
    payload = {
        "sessionID": "17841458811439225",
        "userID": "3NV5OX7PZK_HICOs",
        "newSession": True,
        "msisdn": "233231804643",
        "userData": "*928*309#",
        "network": "MTN",
    }
    resp = client.post(
        "/ussd/callback/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["continueSession"] is True
    assert "Register Business" in data["message"]
    assert "Invalid" not in data["message"]


@pytest.mark.django_db
def test_arkesel_subsequent_dial(client):
    payload = {
        "sessionID": "17841458811439225",
        "userID": "3NV5OX7PZK_HICOs",
        "newSession": True,
        "msisdn": "233231804643",
        "userData": "*928*309#",
        "network": "MTN",
    }
    client.post(
        "/ussd/callback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    follow = {
        **payload,
        "newSession": False,
        "userData": "1",
    }
    resp = client.post(
        "/ussd/callback/",
        data=json.dumps(follow),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["continueSession"] is True
    assert "full name" in data["message"].lower()

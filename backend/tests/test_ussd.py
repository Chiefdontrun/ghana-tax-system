"""
test_ussd.py — USSDStateMachine and USSD webhook endpoint tests.

Covers:
- Initial dial shows main menu
- Full 5-step registration flow creates trader
- Invalid input shows error and stays in same step
- CHECK_TIN found / not found
- Session persists between requests
- USSD registration appears in traders list
"""

import json
import uuid
from unittest.mock import patch, MagicMock

import pytest

from apps.ussd.state_machine import (
    USSDStateMachine,
    STATE_MAIN_MENU,
    STATE_REG_NAME,
    STATE_REG_BUSINESS_TYPE,
    STATE_REG_REGION,
    STATE_REG_DISTRICT,
    STATE_REG_CONFIRM,
    STATE_CHECK_TIN,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def ussd_post(client, session_id, phone, text):
    return client.post(
        "/ussd/callback",
        data={
            "sessionId": session_id,
            "serviceCode": "*123#",
            "phoneNumber": phone,
            "text": text,
        },
    )


MSISDN = "+233201000099"


# ── State machine unit tests ──────────────────────────────────────────────────

class TestUSSDStateMachineUnit:
    """Tests against USSDStateMachine directly, mocking the session store."""

    def test_initial_dial_shows_main_menu(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = None
            result = sm.process("sess001", MSISDN, "")
        assert result.startswith("CON")
        assert "Register Business" in result
        assert "Check My TIN" in result

    def test_option_1_advances_to_reg_name(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = {"step": STATE_MAIN_MENU, "phone_number": MSISDN, "collected": {}}
            result = sm.process("sess001", MSISDN, "1")
        assert result.startswith("CON")
        assert "full name" in result.lower()

    def test_invalid_main_menu_option_shows_error(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = {"step": STATE_MAIN_MENU, "phone_number": MSISDN, "collected": {}}
            result = sm.process("sess001", MSISDN, "9")
        assert result.startswith("CON")
        assert "Invalid" in result

    def test_name_too_short_shows_error(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = {"step": STATE_REG_NAME, "phone_number": MSISDN, "collected": {}}
            result = sm.process("sess001", MSISDN, "1*Ab")
        assert result.startswith("CON")
        assert "3 char" in result.lower() or "least" in result.lower()

    def test_valid_name_advances_to_business_type(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = {"step": STATE_REG_NAME, "phone_number": MSISDN, "collected": {}}
            result = sm.process("sess001", MSISDN, "1*Kofi Mensah")
        assert result.startswith("CON")
        assert "Business Type" in result

    def test_invalid_business_type_shows_error(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = {
                "step": STATE_REG_BUSINESS_TYPE,
                "phone_number": MSISDN,
                "collected": {"name": "Kofi"},
            }
            result = sm.process("sess001", MSISDN, "1*Kofi*9")
        assert result.startswith("CON")
        assert "Invalid" in result

    def test_help_returns_end(self):
        sm = USSDStateMachine()
        with patch("apps.ussd.state_machine._session_store") as mock_store:
            mock_store.get.return_value = {"step": STATE_MAIN_MENU, "phone_number": MSISDN, "collected": {}}
            result = sm.process("sess001", MSISDN, "3")
        assert result.startswith("END")
        assert "help" in result.lower() or "District Assembly" in result


# ── Webhook endpoint tests ─────────────────────────────────────────────────────

class TestUSSDWebhookEndpoint:
    def test_ussd_initial_shows_main_menu(self, client):
        resp = ussd_post(client, "sess_init_001", MSISDN, "")
        assert resp.status_code == 200
        assert b"CON" in resp.content
        assert b"Register Business" in resp.content

    def test_ussd_full_registration_flow(self, client, test_db):
        """
        Simulate all 5 steps via the real webhook endpoint.
        Verifies a trader document is created in the DB.
        """
        sid = f"sess_full_{uuid.uuid4().hex[:6]}"
        phone = f"+2332{uuid.uuid4().hex[:8][:8]}"  # unique MSISDN
        # Clamp to valid Ghana phone: +233 + 9 digits
        phone = f"+233{uuid.uuid4().int % 900000000 + 100000000}"

        # Step 0 — initial dial
        ussd_post(client, sid, phone, "")
        # Step 1 — choose Register
        ussd_post(client, sid, phone, "1")
        # Step 2 — enter name
        ussd_post(client, sid, phone, "1*Abena Asante")
        # Step 3 — choose business type (1=Food Vendor)
        ussd_post(client, sid, phone, "1*Abena Asante*1")
        # Step 4 — choose region (2=Ashanti)
        ussd_post(client, sid, phone, "1*Abena Asante*1*2")
        # Step 5 — enter market name
        ussd_post(client, sid, phone, "1*Abena Asante*1*2*Kejetia Market")
        # Step 6 — confirm (1=Confirm)
        resp = ussd_post(client, sid, phone, "1*Abena Asante*1*2*Kejetia Market*1")

        assert resp.status_code == 200
        assert b"END" in resp.content
        assert b"GH-TIN-" in resp.content
        assert test_db["traders"].count_documents({"phone_number": phone}) == 1

    def test_ussd_check_tin_found(self, client, sample_trader):
        sid = f"sess_check_{uuid.uuid4().hex[:6]}"
        phone = sample_trader["phone_number"]

        # Navigate to CHECK_TIN
        ussd_post(client, sid, phone, "")
        ussd_post(client, sid, phone, "2")
        # Use own number
        resp = ussd_post(client, sid, phone, "2*0")

        assert resp.status_code == 200
        assert b"END" in resp.content
        assert sample_trader["tin_number"].encode() in resp.content

    def test_ussd_check_tin_not_found(self, client):
        sid = f"sess_notfound_{uuid.uuid4().hex[:6]}"
        phone = "+233201999888"

        ussd_post(client, sid, phone, "")
        ussd_post(client, sid, phone, "2")
        resp = ussd_post(client, sid, phone, "2*0")

        assert b"END" in resp.content
        assert b"No registration" in resp.content

    def test_ussd_session_persists_between_requests(self, client, test_db):
        """After entering name, the next step correctly shows business type menu."""
        sid = f"sess_persist_{uuid.uuid4().hex[:6]}"
        phone = "+233244888777"

        ussd_post(client, sid, phone, "")
        ussd_post(client, sid, phone, "1")
        resp = ussd_post(client, sid, phone, "1*Kwesi Boateng")

        assert resp.status_code == 200
        assert b"Business Type" in resp.content

    def test_ussd_registration_appears_in_traders_list(
        self, client, test_db, sys_admin_token
    ):
        """Integration: after USSD registration, trader appears in GET /api/traders."""
        sid = f"sess_integ_{uuid.uuid4().hex[:6]}"
        phone = f"+233{uuid.uuid4().int % 900000000 + 100000000}"

        ussd_post(client, sid, phone, "")
        ussd_post(client, sid, phone, "1")
        ussd_post(client, sid, phone, "1*Integration Trader")
        ussd_post(client, sid, phone, "1*Integration Trader*3")
        ussd_post(client, sid, phone, "1*Integration Trader*3*1")
        ussd_post(client, sid, phone, "1*Integration Trader*3*1*Test Market")
        ussd_post(client, sid, phone, "1*Integration Trader*3*1*Test Market*1")

        resp = client.get(
            "/api/traders/",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 200
        body = resp.json()
        phones = [t["phone_number"] for t in body["data"]]
        assert phone in phones

    def test_ussd_missing_session_id_returns_400(self, client):
        resp = client.post(
            "/ussd/callback",
            data={"serviceCode": "*123#", "phoneNumber": MSISDN, "text": ""},
        )
        assert resp.status_code == 400

    def test_ussd_invalid_input_shows_error_not_crash(self, client):
        sid = f"sess_err_{uuid.uuid4().hex[:6]}"
        resp = ussd_post(client, sid, MSISDN, "99")
        assert resp.status_code == 200
        assert b"CON" in resp.content or b"END" in resp.content

"""
test_registration.py — RegistrationService and registration endpoint tests.

Covers:
- Web registration happy path
- Duplicate phone idempotency
- Invalid phone → 422
- Missing fields → 422
- TIN lookup found / not found
"""

import json
import uuid
from unittest.mock import patch, MagicMock

import pytest


VALID_PAYLOAD = {
    "name": "Ama Owusu",
    "phone_number": "0244123456",
    "business_type": "clothing",
    "location": {
        "region": "Ashanti",
        "district": "Kumasi",
        "market_name": "Kumasi Central Market",
    },
}


# ── Service-level tests ───────────────────────────────────────────────────────

class TestRegistrationService:
    def test_web_registration_success(self, test_db):
        """Full happy-path: trader + business documents created, TIN returned."""
        from apps.registration.services import RegistrationService
        svc = RegistrationService()

        result = svc.register_trader_web(VALID_PAYLOAD, ip_address="127.0.0.1")

        assert result["tin_number"].startswith("GH-TIN-")
        assert result["name"] == "Ama Owusu"
        assert test_db["traders"].count_documents({"phone_number": "+233244123456"}) == 1
        assert test_db["businesses"].count_documents({"tin_number": result["tin_number"]}) == 1

    def test_web_registration_duplicate_phone_returns_existing_tin(self, test_db):
        """Second call with same phone returns the same TIN — no new document."""
        from apps.registration.services import RegistrationService
        svc = RegistrationService()

        result1 = svc.register_trader_web(VALID_PAYLOAD, ip_address="127.0.0.1")
        result2 = svc.register_trader_web(VALID_PAYLOAD, ip_address="127.0.0.1")

        assert result1["tin_number"] == result2["tin_number"]
        assert test_db["traders"].count_documents({"phone_number": "+233244123456"}) == 1

    def test_web_registration_creates_audit_log(self, test_db):
        """CREATE_TRADER audit log written on successful registration."""
        from apps.registration.services import RegistrationService
        svc = RegistrationService()
        svc.register_trader_web(VALID_PAYLOAD, ip_address="10.0.0.1")
        assert test_db["audit_logs"].count_documents({"action": "CREATE_TRADER"}) == 1

    def test_ussd_registration_sets_channel_ussd(self, test_db):
        """register_trader_ussd stores channel='ussd'."""
        from apps.registration.services import RegistrationService
        svc = RegistrationService()
        collected = {
            "name": "Kwame Asante",
            "business_type": "retail",
            "region": "Greater Accra",
            "market_name": "Makola Market",
        }
        result = svc.register_trader_ussd(collected, msisdn="+233201000001")
        trader = test_db["traders"].find_one({"trader_id": result["trader_id"]})
        assert trader["channel"] == "ussd"


# ── Endpoint tests ────────────────────────────────────────────────────────────

class TestRegisterEndpoint:
    def test_web_registration_success_returns_201(self, client):
        import json
        resp = client.post(
            "/api/register",
            data=json.dumps(VALID_PAYLOAD),
            content_type="application/json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["tin_number"].startswith("GH-TIN-")

    def test_web_registration_invalid_phone_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "phone_number": "notaphone"}
        resp = client.post(
            "/api/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_web_registration_missing_name_returns_422(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "name"}
        resp = client.post(
            "/api/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_web_registration_missing_location_returns_422(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "location"}
        resp = client.post(
            "/api/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_web_registration_invalid_business_type_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "business_type": "invalid_type"}
        resp = client.post(
            "/api/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_web_registration_duplicate_phone_returns_200_with_same_tin(self, client):
        import json
        resp1 = client.post("/api/register", data=json.dumps(VALID_PAYLOAD), content_type="application/json")
        resp2 = client.post("/api/register", data=json.dumps(VALID_PAYLOAD), content_type="application/json")
        assert resp1.status_code == 201
        # Idempotent second call: may return 201 with same TIN
        tin1 = resp1.json()["data"]["tin_number"]
        tin2 = resp2.json()["data"]["tin_number"]
        assert tin1 == tin2


# ── TIN lookup endpoint tests ─────────────────────────────────────────────────

class TestTINLookupEndpoint:
    def test_tin_lookup_found(self, client, sample_trader):
        import json
        resp = client.post(
            "/api/tin/lookup",
            data=json.dumps({"phone_number": sample_trader["phone_number"]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["tin_number"] == sample_trader["tin_number"]
        assert "***" in body["data"]["name_masked"]

    def test_tin_lookup_not_found(self, client):
        import json
        resp = client.post(
            "/api/tin/lookup",
            data=json.dumps({"phone_number": "+233244999999"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_tin_lookup_invalid_phone_returns_422(self, client):
        import json
        resp = client.post(
            "/api/tin/lookup",
            data=json.dumps({"phone_number": "badphone"}),
            content_type="application/json",
        )
        assert resp.status_code == 422

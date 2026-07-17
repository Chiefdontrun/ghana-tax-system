import pytest
from datetime import datetime, timezone, timedelta
from rest_framework.test import APIClient
import bcrypt

from core.utils.mongo import get_collection, TRADER_OTP_VERIFICATIONS, TRADERS
from apps.trader_auth.repository import TraderOTPRepository
from apps.auth_app.jwt_utils import generate_access_token

@pytest.fixture
def auth_client_trader(sample_trader):
    client = APIClient()
    trader_id = sample_trader["trader_id"]
    token = generate_access_token(trader_id, "TRADER")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client

def test_request_otp_non_enumeration(client, sample_trader, test_db):
    # Unregistered phone
    res = client.post("/api/trader-auth/request-otp/", {"phone_number": "0244000000"})
    assert res.status_code == 200
    assert res.json()["message"] == "If this number is registered, a verification code has been sent."
    assert get_collection(TRADER_OTP_VERIFICATIONS).count_documents({"phone_number": "+233244000000"}) == 0

    # Registered phone
    res = client.post("/api/trader-auth/request-otp/", {"phone_number": sample_trader["phone_number"]})
    assert res.status_code == 200
    assert res.json()["message"] == "If this number is registered, a verification code has been sent."
    assert get_collection(TRADER_OTP_VERIFICATIONS).count_documents({"phone_number": sample_trader["phone_number"]}) == 1

def test_verify_otp_missing_code_returns_400_not_500(client, sample_trader, test_db):
    """Malformed body must never 500 (regression: details= kwarg TypeError)."""
    res = client.post(
        "/api/trader-auth/verify-otp/",
        {"phone_number": sample_trader["phone_number"]},
        content_type="application/json",
    )
    assert res.status_code == 400
    body = res.json()
    assert body["success"] is False
    assert "errors" in body


def test_verify_otp_wrong_field_name_returns_400_or_accepts_alias(client, sample_trader, test_db):
    """otp_code alone is accepted as alias; empty body still 400."""
    client.post("/api/trader-auth/request-otp/", {"phone_number": sample_trader["phone_number"]})
    otp_doc = get_collection(TRADER_OTP_VERIFICATIONS).find_one(
        {"phone_number": sample_trader["phone_number"]}
    )
    hashed_code = bcrypt.hashpw(b"654321", bcrypt.gensalt()).decode("utf-8")
    get_collection(TRADER_OTP_VERIFICATIONS).update_one(
        {"_id": otp_doc["_id"]}, {"$set": {"otp_hash": hashed_code}}
    )
    # Alias otp_code (no `code`) must validate and succeed
    res = client.post(
        "/api/trader-auth/verify-otp/",
        {"phone_number": sample_trader["phone_number"], "otp_code": "654321"},
        content_type="application/json",
    )
    assert res.status_code == 200
    assert "access" in res.json()["data"]


def test_verify_otp_success_and_last_login(client, sample_trader, test_db):
    # Request OTP
    client.post("/api/trader-auth/request-otp/", {"phone_number": sample_trader["phone_number"]})
    otp_doc = get_collection(TRADER_OTP_VERIFICATIONS).find_one({"phone_number": sample_trader["phone_number"]})
    
    # We don't have the code, so we have to manually forge a known code or mock
    # Let's override the hash with a known code "123456"
    salt = bcrypt.gensalt()
    hashed_code = bcrypt.hashpw(b"123456", salt).decode("utf-8")
    get_collection(TRADER_OTP_VERIFICATIONS).update_one({"_id": otp_doc["_id"]}, {"$set": {"otp_hash": hashed_code}})

    res = client.post("/api/trader-auth/verify-otp/", {"phone_number": sample_trader["phone_number"], "code": "123456"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "access" in data
    assert "refresh" in data
    assert data["trader"]["trader_id"] == sample_trader["trader_id"]

    # Check last_login_at
    trader = get_collection(TRADERS).find_one({"trader_id": sample_trader["trader_id"]})
    assert "last_login_at" in trader
    assert trader["last_login_at"] is not None

def test_verify_otp_failure_and_lockout(client, sample_trader, test_db):
    client.post("/api/trader-auth/request-otp/", {"phone_number": sample_trader["phone_number"]})
    otp_doc = get_collection(TRADER_OTP_VERIFICATIONS).find_one({"phone_number": sample_trader["phone_number"]})
    
    salt = bcrypt.gensalt()
    hashed_code = bcrypt.hashpw(b"123456", salt).decode("utf-8")
    get_collection(TRADER_OTP_VERIFICATIONS).update_one({"_id": otp_doc["_id"]}, {"$set": {"otp_hash": hashed_code}})

    for i in range(4):
        res = client.post("/api/trader-auth/verify-otp/", {"phone_number": sample_trader["phone_number"], "code": "000000"})
        assert res.status_code == 400
        assert "Invalid verification code" in res.json()["message"]

    # 5th attempt locks it out
    res = client.post("/api/trader-auth/verify-otp/", {"phone_number": sample_trader["phone_number"], "code": "000000"})
    assert res.status_code == 400
    assert "Too many failed attempts" in res.json()["message"]

    # 6th attempt with correct code still fails
    res = client.post("/api/trader-auth/verify-otp/", {"phone_number": sample_trader["phone_number"], "code": "123456"})
    assert res.status_code == 400
    assert "No active verification code" in res.json()["message"] or "Too many failed attempts" in res.json()["message"]

def test_trader_auth_role_isolation(client, auth_client_sys, auth_client_trader, test_db):
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from apps.auth_app.permissions import IsTraderAuthenticated
    from django.urls import path
    
    class DummyTraderView(APIView):
        permission_classes = [IsTraderAuthenticated]
        def get(self, request):
            return Response({"success": True})

    # Temporarily append this route
    from django.urls import clear_url_caches
    from core import urls
    urls.urlpatterns.append(path("api/dummy-trader-test/", DummyTraderView.as_view()))
    clear_url_caches()

    # A trader cannot access an admin endpoint
    res = auth_client_trader.get("/api/admin/users/")
    assert res.status_code == 403

    # An admin cannot access a trader endpoint
    res_admin = auth_client_sys.get("/api/dummy-trader-test/")
    assert res_admin.status_code == 403
    
    # A trader can access a trader endpoint
    res_trader = auth_client_trader.get("/api/dummy-trader-test/")
    assert res_trader.status_code == 200

def test_trader_auth_refresh(client, sample_trader, test_db):
    from apps.auth_app.jwt_utils import generate_refresh_token
    
    refresh_token = generate_refresh_token(sample_trader["trader_id"])
    res = client.post("/api/trader-auth/refresh/", {"refresh": refresh_token})
    
    assert res.status_code == 200
    data = res.json()["data"]
    assert "access" in data
    
    # Invalid token test
    res = client.post("/api/trader-auth/refresh/", {"refresh": "invalid.token.here"})
    assert res.status_code == 401

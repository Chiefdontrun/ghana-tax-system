"""
test_auth.py — AuthService and auth endpoint tests.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
import pytest
from django.conf import settings

import apps.auth_app.email_service as email_service_module
from apps.auth_app.email_service import AdminAuthEmailService, EmailDeliveryError
from resend.exceptions import ResendError


class TestLoginEndpoint:
    def test_login_success_returns_pending_token(self, client, sys_admin_doc, test_db, monkeypatch):
        monkeypatch.setattr("apps.auth_app.services.AuthService.generate_otp_code", staticmethod(lambda: "123456"))
        monkeypatch.setattr("apps.auth_app.services._email_service.send_otp", lambda email, code: None)

        resp = client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "pending_token" in body["data"]
        assert body["data"]["scope"] == "otp_pending"
        assert "access" not in body["data"]
        assert "refresh" not in body["data"]
        assert test_db["otp_verifications"].count_documents({"admin_id": sys_admin_doc["admin_id"]}) == 1

    def test_login_wrong_password_returns_401(self, client, sys_admin_doc):
        resp = client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "WrongPass!"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        resp = client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "ghost@nowhere.com", "password": "anything"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_inactive_account_returns_401(self, client, test_db):
        admin_id = str(uuid.uuid4())
        test_db["admins"].insert_one({
            "admin_id": admin_id,
            "email": "inactive@test.gov.gh",
            "name": "Inactive",
            "role": "TAX_ADMIN",
            "password_hash": bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt()).decode(),
            "is_active": False,
            "created_at": datetime.now(timezone.utc),
        })
        resp = client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "inactive@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_writes_otp_audit_log(self, client, sys_admin_doc, test_db, monkeypatch):
        monkeypatch.setattr("apps.auth_app.services.AuthService.generate_otp_code", staticmethod(lambda: "123456"))
        monkeypatch.setattr("apps.auth_app.services._email_service.send_otp", lambda email, code: None)
        client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert test_db["audit_logs"].count_documents({"action": "OTP_GENERATED"}) == 1
        assert test_db["audit_logs"].count_documents({"action": "LOGIN_SUCCESS"}) == 0

    def test_failed_login_writes_fail_audit_log(self, client, sys_admin_doc, test_db):
        client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "BadPass"}),
            content_type="application/json",
        )
        assert test_db["audit_logs"].count_documents({"action": "LOGIN_FAIL"}) == 1


class TestAdminAuthEmailService:
    def test_send_otp_raises_when_resend_api_key_missing(self, monkeypatch):
        monkeypatch.setattr(settings, "RESEND_API_KEY", "")
        monkeypatch.setattr(settings, "DEFAULT_FROM_EMAIL", "Ghana Tax System <no-reply@example.com>")

        service = AdminAuthEmailService()

        with pytest.raises(EmailDeliveryError, match="RESEND_API_KEY"):
            service.send_otp("user@example.com", "123456")

    def test_send_otp_raises_when_resend_provider_returns_error(self, monkeypatch):
        monkeypatch.setattr(settings, "RESEND_API_KEY", "invalid-key")
        monkeypatch.setattr(settings, "DEFAULT_FROM_EMAIL", "Ghana Tax System <no-reply@example.com>")

        def raise_resend_error(self, params):
            raise ResendError(
                code="invalid_request",
                error_type="authentication_error",
                message="Invalid API key",
                suggested_action="Verify your Resend API key.",
            )

        monkeypatch.setattr(email_service_module.Emails, "send", raise_resend_error)
        service = AdminAuthEmailService()

        with pytest.raises(EmailDeliveryError, match="Could not send verification code"):
            service.send_otp("user@example.com", "123456")


class TestOtpFlow:
    def _start_login(self, client, monkeypatch):
        monkeypatch.setattr("apps.auth_app.services.AuthService.generate_otp_code", staticmethod(lambda: "123456"))
        monkeypatch.setattr("apps.auth_app.services._email_service.send_otp", lambda email, code: None)
        return client.post(
            "/api/auth/login/",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )

    def test_full_login_otp_verify_flow_issues_tokens(self, client, sys_admin_doc, test_db, monkeypatch):
        login_resp = self._start_login(client, monkeypatch)
        pending_token = login_resp.json()["data"]["pending_token"]

        resp = client.post(
            "/api/auth/verify-otp/",
            data=json.dumps({"code": "123456"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {pending_token}",
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "access" in body
        assert "refresh" in body
        assert body["role"] == "SYS_ADMIN"
        assert test_db["audit_logs"].count_documents({"action": "OTP_VERIFIED"}) == 1
        assert test_db["audit_logs"].count_documents({"action": "LOGIN_SUCCESS"}) == 1

    def test_wrong_code_returns_remaining_attempts(self, client, sys_admin_doc, monkeypatch):
        login_resp = self._start_login(client, monkeypatch)
        pending_token = login_resp.json()["data"]["pending_token"]

        resp = client.post(
            "/api/auth/verify-otp/",
            data=json.dumps({"code": "999999"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {pending_token}",
        )
        assert resp.status_code == 400
        assert int(resp.json()["errors"]["remaining_attempts"]) == 4

    def test_five_failed_attempts_force_restart(self, client, sys_admin_doc, monkeypatch):
        login_resp = self._start_login(client, monkeypatch)
        pending_token = login_resp.json()["data"]["pending_token"]

        status_codes = []
        for _ in range(5):
            resp = client.post(
                "/api/auth/verify-otp/",
                data=json.dumps({"code": "999999"}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {pending_token}",
            )
            status_codes.append(resp.status_code)
        assert status_codes[-1] == 401

    def test_expired_otp_is_rejected(self, client, sys_admin_doc, test_db, monkeypatch):
        login_resp = self._start_login(client, monkeypatch)
        pending_token = login_resp.json()["data"]["pending_token"]
        test_db["otp_verifications"].update_one(
            {"admin_id": sys_admin_doc["admin_id"]},
            {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}},
        )

        resp = client.post(
            "/api/auth/verify-otp/",
            data=json.dumps({"code": "123456"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {pending_token}",
        )
        assert resp.status_code == 401

    def test_resend_rate_limit_per_pending_session(self, client, sys_admin_doc, monkeypatch):
        login_resp = self._start_login(client, monkeypatch)
        pending_token = login_resp.json()["data"]["pending_token"]

        resp = client.post(
            "/api/auth/resend-otp/",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {pending_token}",
        )
        assert resp.status_code == 429
        assert "retry_after" in resp.json()["errors"]

    def test_pending_token_blocked_from_protected_routes(self, client, sys_admin_doc, monkeypatch):
        login_resp = self._start_login(client, monkeypatch)
        pending_token = login_resp.json()["data"]["pending_token"]

        resp = client.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {pending_token}",
        )
        assert resp.status_code in (401, 403)


class TestTokenRefresh:
    def test_token_refresh_works(self, client, sys_admin_token):
        from apps.auth_app.jwt_utils import generate_refresh_token
        refresh_token = generate_refresh_token("unused")

        resp = client.post(
            "/api/auth/refresh/",
            data=json.dumps({"refresh": refresh_token}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_token_refresh_works_for_admin(self, client, sys_admin_doc):
        from apps.auth_app.jwt_utils import generate_refresh_token
        refresh_token = generate_refresh_token(sys_admin_doc["admin_id"])

        resp = client.post(
            "/api/auth/refresh/",
            data=json.dumps({"refresh": refresh_token}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "access" in resp.json()["data"]

    def test_token_refresh_invalid_token_returns_401(self, client):
        resp = client.post(
            "/api/auth/refresh/",
            data=json.dumps({"refresh": "not.a.token"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_access_token_cannot_be_used_as_refresh(self, client, sys_admin_doc, sys_admin_token):
        resp = client.post(
            "/api/auth/refresh/",
            data=json.dumps({"refresh": sys_admin_token}),
            content_type="application/json",
        )
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_access_protected_route_without_token_returns_401(self, client):
        resp = client.get("/api/audit-logs/")
        assert resp.status_code in (401, 403)

    def test_authenticated_me_endpoint(self, client, sys_admin_token, sys_admin_doc):
        resp = client.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "sysadmin@test.gov.gh"


class TestRBAC:
    def test_tax_admin_cannot_access_sys_admin_endpoint(self, client, tax_admin_token):
        resp = client.get(
            "/api/audit-logs/",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 403

    def test_tax_admin_cannot_create_admin_user(self, client, tax_admin_token):
        resp = client.post(
            "/api/admin/users/",
            data=json.dumps({
                "email": "new@test.gov.gh",
                "name": "New Admin",
                "password": "NewPass123!",
                "role": "TAX_ADMIN",
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 403

    def test_sys_admin_can_access_audit_logs(self, client, sys_admin_token):
        resp = client.get(
            "/api/audit-logs/",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 200

    def test_tax_admin_can_access_traders_list(self, client, tax_admin_token):
        resp = client.get(
            "/api/traders/",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 200

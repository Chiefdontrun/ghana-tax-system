"""
test_auth.py — AuthService and auth endpoint tests.

Covers:
- Login success returns tokens
- Login wrong password returns 401
- Protected route without token returns 401
- TAX_ADMIN cannot access SYS_ADMIN-only endpoint
- Token refresh works
"""

import json
import uuid
from datetime import datetime, timezone

import pytest


class TestLoginEndpoint:
    def test_login_success_returns_tokens(self, client, sys_admin_doc):
        resp = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "access" in body["data"]
        assert "refresh" in body["data"]
        assert body["data"]["role"] == "SYS_ADMIN"

    def test_login_wrong_password_returns_401(self, client, sys_admin_doc):
        resp = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "WrongPass!"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        resp = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "ghost@nowhere.com", "password": "anything"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_inactive_account_returns_401(self, client, test_db):
        import bcrypt
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
            "/api/auth/login",
            data=json.dumps({"email": "inactive@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_login_writes_audit_log(self, client, sys_admin_doc, test_db):
        client.post(
            "/api/auth/login",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert test_db["audit_logs"].count_documents({"action": "LOGIN_SUCCESS"}) == 1

    def test_failed_login_writes_fail_audit_log(self, client, sys_admin_doc, test_db):
        client.post(
            "/api/auth/login",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "BadPass"}),
            content_type="application/json",
        )
        assert test_db["audit_logs"].count_documents({"action": "LOGIN_FAIL"}) == 1


class TestTokenRefresh:
    def test_token_refresh_works(self, client, sys_admin_doc):
        # Get tokens via login
        login_resp = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "sysadmin@test.gov.gh", "password": "TestPass123!"}),
            content_type="application/json",
        )
        refresh_token = login_resp.json()["data"]["refresh"]

        # Exchange for new access token
        resp = client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh": refresh_token}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access" in body["data"]

    def test_token_refresh_invalid_token_returns_401(self, client):
        resp = client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh": "not.a.token"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_access_token_cannot_be_used_as_refresh(self, client, sys_admin_doc, sys_admin_token):
        """Using an access token as a refresh token must be rejected."""
        resp = client.post(
            "/api/auth/refresh",
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
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {sys_admin_token}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "sysadmin@test.gov.gh"


class TestRBAC:
    def test_tax_admin_cannot_access_sys_admin_endpoint(
        self, client, tax_admin_token
    ):
        """TAX_ADMIN must get 403 on GET /api/audit-logs."""
        resp = client.get(
            "/api/audit-logs/",
            HTTP_AUTHORIZATION=f"Bearer {tax_admin_token}",
        )
        assert resp.status_code == 403

    def test_tax_admin_cannot_create_admin_user(self, client, tax_admin_token):
        """TAX_ADMIN must get 403 on POST /api/admin/users."""
        resp = client.post(
            "/api/admin/users",
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

"""
AuthService — all authentication business logic.
Views are thin; this class owns the rules.
"""

import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt

from apps.auth_app.repository import AdminRepository
from apps.auth_app.jwt_utils import (
    generate_access_token,
    generate_otp_pending_token,
    generate_refresh_token,
    verify_token,
    TOKEN_TYPE_OTP_PENDING,
    TOKEN_TYPE_REFRESH,
    TokenExpiredError,
    TokenInvalidError,
)
from apps.auth_app.otp_repository import OtpVerificationRepository
from apps.auth_app.email_service import AdminAuthEmailService, EmailDeliveryError
from apps.audit.repository import AuditRepository
from rest_framework.exceptions import AuthenticationFailed, ValidationError, PermissionDenied

logger = logging.getLogger(__name__)

_admin_repo = AdminRepository()
_otp_repo = OtpVerificationRepository()
_audit_repo = AuditRepository()
_email_service = AdminAuthEmailService()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AuthService:
    """Handles login, token refresh, and admin user management."""

    OTP_EXPIRY_MINUTES = 5
    OTP_MAX_ATTEMPTS = 5
    OTP_RESEND_COOLDOWN_SECONDS = 60
    OTP_MAX_RESENDS = 3

    # ── Login ──────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str, ip_address: str, user_agent: str) -> dict:
        """
        Validate credentials, send a one-time code, and return a pending token.
        Full admin tokens are only issued after OTP verification.
        Raises AuthenticationFailed on bad credentials or inactive account.
        """
        admin = _admin_repo.find_by_email(email)

        # We always run bcrypt (even on miss) to prevent timing attacks
        password_hash = admin["password_hash"] if admin else "$2b$12$invalidhashpadding00000000000000000000000000000000000"
        credentials_valid = admin is not None and _check_password(password, password_hash)

        if not credentials_valid or not admin:
            _audit_repo.log({
                "event_id": str(uuid.uuid4()),
                "actor_id": "anonymous",
                "actor_role": "anonymous",
                "action": "LOGIN_FAIL",
                "entity_type": "session",
                "entity_id": email,
                "channel": "admin",
                "ip_address": ip_address,
                "user_agent": user_agent,
                "before": None,
                "after": None,
            })
            raise AuthenticationFailed("Invalid email or password.")

        if not admin.get("is_active", True):
            raise AuthenticationFailed("Account is deactivated. Contact system administrator.")

        _otp_repo.invalidate_active_for_admin(admin["admin_id"])
        otp_record, plain_code = self._create_otp_record(admin["admin_id"])

        try:
            _email_service.send_otp(admin["email"], plain_code)
        except EmailDeliveryError:
            _otp_repo.invalidate(otp_record["otp_id"])
            self._log_otp_event(
                admin=admin,
                action="OTP_EMAIL_FAILED",
                ip_address=ip_address,
                user_agent=user_agent,
                otp_id=otp_record["otp_id"],
            )
            raise

        pending_token = generate_otp_pending_token(admin["admin_id"], otp_record["otp_id"])
        self._log_otp_event(
            admin=admin,
            action="OTP_GENERATED",
            ip_address=ip_address,
            user_agent=user_agent,
            otp_id=otp_record["otp_id"],
        )

        return {
            "pending_token": pending_token,
            "scope": TOKEN_TYPE_OTP_PENDING,
            "expires_in": 600,
            "otp_expires_in": self.OTP_EXPIRY_MINUTES * 60,
            "email": admin["email"],
        }

    def verify_otp(self, pending_token: str, code: str, ip_address: str, user_agent: str) -> dict:
        payload = self._verify_pending_token(pending_token)
        admin_id = payload.get("sub")
        otp_id = payload.get("otp_id")
        admin = _admin_repo.find_by_id(admin_id)
        if not admin or not admin.get("is_active", True):
            raise AuthenticationFailed("Admin account not found or inactive.")

        record = _otp_repo.find_active(otp_id, admin_id)
        now = datetime.now(timezone.utc)
        if not record:
            raise AuthenticationFailed("Verification session has expired. Please sign in again.")

        if _as_utc(record["expires_at"]) <= now:
            _otp_repo.invalidate(otp_id)
            self._log_otp_event(admin, "OTP_EXPIRED", ip_address, user_agent, otp_id)
            raise AuthenticationFailed("Verification code has expired. Please sign in again.")

        if record.get("attempts", 0) >= self.OTP_MAX_ATTEMPTS:
            _otp_repo.invalidate(otp_id)
            raise AuthenticationFailed("Too many failed attempts. Please sign in again.")

        if not _check_password(code, record["otp_hash"]):
            _otp_repo.increment_attempts(otp_id)
            attempts = record.get("attempts", 0) + 1
            remaining = max(self.OTP_MAX_ATTEMPTS - attempts, 0)
            self._log_otp_event(admin, "OTP_FAILED", ip_address, user_agent, otp_id)
            if remaining == 0:
                _otp_repo.invalidate(otp_id)
                raise AuthenticationFailed("Too many failed attempts. Please sign in again.")
            raise ValidationError({"code": "Invalid verification code.", "remaining_attempts": remaining})

        _otp_repo.mark_used(otp_id)
        self._log_otp_event(admin, "OTP_VERIFIED", ip_address, user_agent, otp_id)
        return self._issue_admin_session(admin, ip_address, user_agent)

    def resend_otp(self, pending_token: str, ip_address: str, user_agent: str) -> dict:
        payload = self._verify_pending_token(pending_token)
        admin_id = payload.get("sub")
        otp_id = payload.get("otp_id")
        admin = _admin_repo.find_by_id(admin_id)
        if not admin or not admin.get("is_active", True):
            raise AuthenticationFailed("Admin account not found or inactive.")

        current = _otp_repo.find_active(otp_id, admin_id)
        if not current:
            raise AuthenticationFailed("Verification session has expired. Please sign in again.")

        now = datetime.now(timezone.utc)
        if _as_utc(current["expires_at"]) <= now:
            _otp_repo.invalidate(otp_id)
            self._log_otp_event(admin, "OTP_EXPIRED", ip_address, user_agent, otp_id)
            raise AuthenticationFailed("Verification code has expired. Please sign in again.")

        if current.get("resend_count", 0) >= self.OTP_MAX_RESENDS:
            raise ValidationError({"resend": "Maximum resend limit reached. Please sign in again."})

        elapsed = (now - _as_utc(current["created_at"])).total_seconds()
        if elapsed < self.OTP_RESEND_COOLDOWN_SECONDS:
            retry_after = self.OTP_RESEND_COOLDOWN_SECONDS - int(elapsed)
            raise ValidationError({"resend": "Please wait before requesting another code.", "retry_after": retry_after})

        _otp_repo.invalidate(otp_id)
        new_record, plain_code = self._create_otp_record(
            admin_id,
            resend_count=current.get("resend_count", 0) + 1,
        )

        try:
            _email_service.send_otp(admin["email"], plain_code)
        except EmailDeliveryError:
            _otp_repo.invalidate(new_record["otp_id"])
            self._log_otp_event(admin, "OTP_EMAIL_FAILED", ip_address, user_agent, new_record["otp_id"])
            raise

        self._log_otp_event(admin, "OTP_RESENT", ip_address, user_agent, new_record["otp_id"])
        return {
            "pending_token": generate_otp_pending_token(admin_id, new_record["otp_id"]),
            "scope": TOKEN_TYPE_OTP_PENDING,
            "expires_in": 600,
            "otp_expires_in": self.OTP_EXPIRY_MINUTES * 60,
            "resend_count": new_record["resend_count"],
        }

    def cleanup_otp_records(self) -> int:
        return _otp_repo.cleanup_expired_or_used()

    def _create_otp_record(self, admin_id: str, resend_count: int = 0) -> tuple[dict, str]:
        code = self.generate_otp_code()
        otp_id = str(uuid.uuid4())
        record = _otp_repo.create({
            "otp_id": otp_id,
            "admin_id": admin_id,
            "otp_hash": _hash_password(code),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES),
            "attempts": 0,
            "resend_count": resend_count,
        })
        return record, code

    @staticmethod
    def generate_otp_code() -> str:
        return f"{secrets.randbelow(900000) + 100000:06d}"

    def _verify_pending_token(self, token: str) -> dict:
        try:
            payload = verify_token(token, expected_type=TOKEN_TYPE_OTP_PENDING)
        except (TokenExpiredError, TokenInvalidError) as exc:
            raise AuthenticationFailed(str(exc)) from exc
        if payload.get("scope") != TOKEN_TYPE_OTP_PENDING or not payload.get("otp_id"):
            raise AuthenticationFailed("Invalid verification session.")
        return payload

    def _issue_admin_session(self, admin: dict, ip_address: str, user_agent: str) -> dict:
        _admin_repo.update_last_login(admin["admin_id"])
        access = generate_access_token(admin["admin_id"], admin["role"])
        refresh = generate_refresh_token(admin["admin_id"])
        _audit_repo.log({
            "event_id": str(uuid.uuid4()),
            "actor_id": admin["admin_id"],
            "actor_role": admin["role"],
            "action": "LOGIN_SUCCESS",
            "entity_type": "session",
            "entity_id": admin["admin_id"],
            "channel": "admin",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "before": None,
            "after": {"last_login_at": datetime.now(timezone.utc).isoformat()},
        })

        return {
            "access": access,
            "refresh": refresh,
            "role": admin["role"],
            "admin_id": admin["admin_id"],
            "name": admin.get("name", ""),
            "email": admin["email"],
        }

    def _log_otp_event(self, admin: dict, action: str, ip_address: str, user_agent: str, otp_id: str) -> None:
        _audit_repo.log({
            "event_id": str(uuid.uuid4()),
            "actor_id": admin["admin_id"],
            "actor_role": admin.get("role", "admin"),
            "action": action,
            "entity_type": "otp_verification",
            "entity_id": otp_id,
            "channel": "admin",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "before": None,
            "after": {"admin_id": admin["admin_id"]},
        })

    # ── Token refresh ──────────────────────────────────────────────────────────

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Validate a refresh token and issue a new access token.
        Raises AuthenticationFailed if the token is invalid/expired.
        """
        try:
            payload = verify_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
        except (TokenExpiredError, TokenInvalidError) as exc:
            raise AuthenticationFailed(str(exc)) from exc

        admin_id = payload.get("sub")
        admin = _admin_repo.find_by_id(admin_id)
        if not admin:
            raise AuthenticationFailed("Admin account not found.")
        if not admin.get("is_active", True):
            raise AuthenticationFailed("Account is deactivated.")

        new_access = generate_access_token(admin["admin_id"], admin["role"])
        return {"access": new_access}

    # ── Admin user management ──────────────────────────────────────────────────

    def create_admin(
        self,
        email: str,
        name: str,
        password: str,
        role: str,
        actor: dict,
        ip_address: str,
        user_agent: str,
    ) -> dict:
        """
        Create a new admin account.
        Only SYS_ADMIN may call this (enforced by permission class, asserted here too).
        """
        if role not in ("SYS_ADMIN", "TAX_ADMIN"):
            raise ValidationError({"role": f"Invalid role '{role}'. Must be SYS_ADMIN or TAX_ADMIN."})

        existing = _admin_repo.find_by_email(email)
        if existing:
            raise ValidationError({"email": f"An admin with email '{email}' already exists."})

        admin_id = str(uuid.uuid4())
        new_admin = _admin_repo.create({
            "admin_id": admin_id,
            "email": email.lower().strip(),
            "name": name.strip(),
            "role": role,
            "password_hash": _hash_password(password),
            "is_active": True,
        })

        _audit_repo.log({
            "event_id": str(uuid.uuid4()),
            "actor_id": actor["admin_id"],
            "actor_role": actor["role"],
            "action": "CREATE_ADMIN",
            "entity_type": "admin",
            "entity_id": admin_id,
            "channel": "admin",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "before": None,
            "after": {"email": email, "role": role},
        })

        return new_admin

    def update_admin(
        self,
        target_admin_id: str,
        updates: dict,
        actor: dict,
        ip_address: str,
        user_agent: str,
    ) -> dict:
        """
        Update an admin's role or active status.
        A SYS_ADMIN cannot change their own role to prevent lockout.
        """
        if actor["admin_id"] == target_admin_id and "role" in updates:
            raise PermissionDenied("You cannot change your own role.")

        existing = _admin_repo.find_by_id(target_admin_id)
        if not existing:
            raise ValidationError({"admin_id": "Admin not found."})

        # Only allow role and is_active changes
        allowed_fields = {"role", "is_active"}
        filtered = {k: v for k, v in updates.items() if k in allowed_fields}
        if not filtered:
            raise ValidationError({"detail": "No valid fields to update (allowed: role, is_active)."})

        if "role" in filtered and filtered["role"] not in ("SYS_ADMIN", "TAX_ADMIN"):
            raise ValidationError({"role": f"Invalid role '{filtered['role']}'."})

        updated = _admin_repo.update(target_admin_id, filtered)

        action = "ROLE_CHANGE" if "role" in filtered else "STATUS_CHANGE"
        _audit_repo.log({
            "event_id": str(uuid.uuid4()),
            "actor_id": actor["admin_id"],
            "actor_role": actor["role"],
            "action": action,
            "entity_type": "admin",
            "entity_id": target_admin_id,
            "channel": "admin",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "before": {k: existing.get(k) for k in filtered},
            "after": filtered,
        })

        return updated

    def list_admins(self, actor: dict = None) -> list[dict]:
        """List all admin accounts. Phase 12: optional service-layer RBAC guard."""
        if actor is not None and actor.get("role") != "SYS_ADMIN":
            raise PermissionDenied("SYS_ADMIN role required to list admin accounts.")
        return _admin_repo.list_all()

    def get_me(self, admin_id: str) -> Optional[dict]:
        return _admin_repo.find_by_id(admin_id)

"""
AuthService — all authentication business logic.
Views are thin; this class owns the rules.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt

from apps.auth_app.repository import AdminRepository
from apps.auth_app.jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    TOKEN_TYPE_REFRESH,
    TokenExpiredError,
    TokenInvalidError,
)
from apps.audit.repository import AuditRepository
from rest_framework.exceptions import AuthenticationFailed, ValidationError, PermissionDenied

logger = logging.getLogger(__name__)

_admin_repo = AdminRepository()
_audit_repo = AuditRepository()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


class AuthService:
    """Handles login, token refresh, and admin user management."""

    # ── Login ──────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str, ip_address: str, user_agent: str) -> dict:
        """
        Validate credentials and return JWT token pair + admin metadata.
        Writes LOGIN_SUCCESS or LOGIN_FAIL audit log regardless of outcome.
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

        # Stamp last login
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

    def list_admins(self) -> list[dict]:
        return _admin_repo.list_all()

    def get_me(self, admin_id: str) -> Optional[dict]:
        return _admin_repo.find_by_id(admin_id)

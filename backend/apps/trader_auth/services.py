"""
TraderAuthService — Handles OTP generation, verification, and token issuance for traders.
"""

import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import bcrypt

from apps.trader_auth.repository import TraderOTPRepository
from apps.registration.repository import TraderRepository
from apps.notifications.services import NotificationService
from apps.auth_app.jwt_utils import generate_access_token, generate_refresh_token
from apps.audit.repository import AuditRepository

logger = logging.getLogger(__name__)


class RateLimitedError(Exception):
    pass


class TraderAuthService:
    def __init__(self):
        self._otp_repo = TraderOTPRepository()
        self._trader_repo = TraderRepository()
        self._notification_service = NotificationService()
        self._audit_repo = AuditRepository()

    def request_otp(self, phone: str, request_info: dict) -> str:
        """
        Request a verification code for a trader.
        Always returns a generic success message to prevent enumeration.
        """
        trader = self._trader_repo.find_by_phone(phone)
        if not trader:
            self._audit_repo.log({
                "action": "TRADER_LOGIN_OTP_REQUESTED",
                "actor_id": "anonymous",
                "actor_role": "ANONYMOUS",
                "entity_id": phone,
                "channel": "web",
                "ip_address": request_info.get("ip_address"),
                "user_agent": request_info.get("user_agent"),
                "meta": {"status": "not_found_skipped"},
            })
            return "If this number is registered, a verification code has been sent."

        trader_id = trader["trader_id"]

        latest = self._otp_repo.latest_for_phone(phone)
        if latest:
            now = datetime.now(timezone.utc)
            # 60s cooldown
            if (now - latest["created_at"]).total_seconds() < 60:
                raise RateLimitedError("Please wait 60 seconds before requesting a new code.")

        self._otp_repo.invalidate_active_for_phone(phone)

        code = f"{secrets.randbelow(1000000):06d}"
        salt = bcrypt.gensalt()
        hashed_code = bcrypt.hashpw(code.encode("utf-8"), salt).decode("utf-8")

        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=5)
        otp_id = str(uuid.uuid4())

        self._otp_repo.create({
            "otp_id": otp_id,
            "trader_id": trader_id,
            "phone_number": phone,
            "otp_hash": hashed_code,
            "expires_at": expires,
        })

        self._notification_service.send_otp_sms(phone, code)

        self._audit_repo.log({
            "action": "TRADER_LOGIN_OTP_REQUESTED",
            "actor_id": trader_id,
            "actor_role": "TRADER",
            "entity_id": trader_id,
            "channel": "web",
            "ip_address": request_info.get("ip_address"),
            "user_agent": request_info.get("user_agent"),
            "meta": {"status": "sent"},
        })

        return "If this number is registered, a verification code has been sent."

    def verify_otp(self, phone: str, code: str, request_info: dict) -> Tuple[dict, dict]:
        """
        Verify the OTP code and issue JWT tokens on success.
        Returns: (tokens_dict, profile_dict)
        """
        active_otp = self._otp_repo.find_active(phone)
        if not active_otp:
            self._log_failed_attempt(phone, "no_active_otp", request_info)
            raise ValueError("No active verification code found or code expired.")

        otp_id = active_otp["otp_id"]
        trader_id = active_otp["trader_id"]

        # Check attempts
        if active_otp.get("attempts", 0) >= 5:
            self._otp_repo.invalidate(otp_id)
            self._log_failed_attempt(phone, "locked_out", request_info, trader_id)
            raise ValueError("Too many failed attempts. Please request a new code.")

        is_valid = bcrypt.checkpw(code.encode("utf-8"), active_otp["otp_hash"].encode("utf-8"))
        if not is_valid:
            self._otp_repo.increment_attempts(otp_id)
            self._log_failed_attempt(phone, "invalid_code", request_info, trader_id)
            
            # Check if this was the 5th attempt
            if active_otp.get("attempts", 0) + 1 >= 5:
                self._otp_repo.invalidate(otp_id)
                raise ValueError("Too many failed attempts. Please request a new code.")
                
            raise ValueError("Invalid verification code.")

        self._otp_repo.mark_used(otp_id)
        
        # Stamp last_login_at
        now = datetime.now(timezone.utc)
        self._trader_repo.update(trader_id, {"last_login_at": now})

        # Generate tokens
        access_token = generate_access_token(trader_id, "TRADER")
        refresh_token = generate_refresh_token(trader_id)

        trader = self._trader_repo.find_by_id(trader_id)
        
        self._audit_repo.log({
            "action": "TRADER_LOGIN_OTP_VERIFIED",
            "actor_id": trader_id,
            "actor_role": "TRADER",
            "entity_id": trader_id,
            "channel": "web",
            "ip_address": request_info.get("ip_address"),
            "user_agent": request_info.get("user_agent"),
        })

        tokens = {
            "access": access_token,
            "refresh": refresh_token,
        }
        profile = {
            "trader_id": trader_id,
            "name": trader["name"],
            "phone_number": trader["phone_number"],
        }
        return tokens, profile

    def _log_failed_attempt(self, phone: str, reason: str, request_info: dict, trader_id: Optional[str] = None):
        self._audit_repo.log({
            "action": "TRADER_LOGIN_FAILED",
            "actor_id": trader_id or "anonymous",
            "actor_role": "TRADER" if trader_id else "ANONYMOUS",
            "entity_id": phone,
            "channel": "web",
            "ip_address": request_info.get("ip_address"),
            "user_agent": request_info.get("user_agent"),
            "meta": {"reason": reason},
        })

"""
JWT utilities for ghana-tax-system.
All token generation and verification logic lives here.
No business logic — pure cryptographic operations.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

# ── Token type constants ───────────────────────────────────────────────────────
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_OTP_PENDING = "otp_pending"

# ── Custom exceptions ─────────────────────────────────────────────────────────

class TokenExpiredError(AuthenticationFailed):
    default_detail = "Token has expired."
    default_code = "token_expired"


class TokenInvalidError(AuthenticationFailed):
    default_detail = "Token is invalid."
    default_code = "token_invalid"


# ── Token generation ──────────────────────────────────────────────────────────

def generate_access_token(admin_id: str, role: str) -> str:
    """
    Generate a short-lived JWT access token.
    Payload: {sub, role, type, iat, exp}
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": admin_id,
        "role": role,
        "type": TOKEN_TYPE_ACCESS,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def generate_refresh_token(admin_id: str) -> str:
    """
    Generate a long-lived JWT refresh token.
    Payload: {sub, type, iat, exp}
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": admin_id,
        "type": TOKEN_TYPE_REFRESH,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def generate_otp_pending_token(admin_id: str, otp_id: str) -> str:
    """
    Generate a short-lived token that can only be used to finish OTP verification.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=10)
    payload = {
        "sub": admin_id,
        "otp_id": otp_id,
        "scope": TOKEN_TYPE_OTP_PENDING,
        "type": TOKEN_TYPE_OTP_PENDING,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


# ── Token verification ────────────────────────────────────────────────────────

def verify_token(token: str, expected_type: Optional[str] = None) -> dict:
    """
    Decode and verify a JWT token.
    Raises TokenExpiredError or TokenInvalidError on failure.
    If expected_type is provided, raises TokenInvalidError if the token type
    doesn't match (prevents using a refresh token as an access token).
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT decode failed: %s", exc)
        raise TokenInvalidError()

    if expected_type and payload.get("type") != expected_type:
        raise TokenInvalidError(
            f"Expected token type '{expected_type}', got '{payload.get('type')}'."
        )

    return payload


def get_token_from_request(request) -> Optional[str]:
    """
    Extract the Bearer token from the Authorization header.
    Returns None if the header is absent or malformed.
    """
    auth_header: str = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):].strip()
    return token if token else None

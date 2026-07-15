"""
JWTAuthentication — DRF authentication backend.
Replaces the Phase 1 stub. Validates the Bearer token on every protected request
and attaches the admin document to request.admin.
"""

import logging
from typing import Optional, Tuple

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.auth_app.jwt_utils import (
    get_token_from_request,
    verify_token,
    TOKEN_TYPE_ACCESS,
    TokenExpiredError,
    TokenInvalidError,
)
from apps.auth_app.repository import AdminRepository

logger = logging.getLogger(__name__)

_admin_repo = AdminRepository()


class JWTAuthentication(BaseAuthentication):
    """
    Validates Bearer JWT access tokens.
    On success: returns (admin_dict, token_payload).
    On missing header: returns None (allows anonymous access for public endpoints).
    On invalid/expired token: raises AuthenticationFailed.
    """

    def authenticate(self, request) -> Optional[Tuple[dict, dict]]:
        token = get_token_from_request(request)
        if token is None:
            return None  # No token — let permission classes reject if required

        try:
            payload = verify_token(token, expected_type=TOKEN_TYPE_ACCESS)
        except (TokenExpiredError, TokenInvalidError) as exc:
            raise AuthenticationFailed(str(exc)) from exc

        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id:
            raise AuthenticationFailed("Token payload missing 'sub' field.")

        if role == "TRADER":
            from apps.registration.repository import TraderRepository
            trader = TraderRepository().find_by_id(user_id)
            if not trader:
                raise AuthenticationFailed("Trader account not found.")
            
            # The spec notes traders don't currently have an is_active field
            if trader.get("is_active", True) is False:
                raise AuthenticationFailed("Trader account is deactivated.")

            request.trader = trader
            request.user = trader  # Sets DRF request.user
            # Return tuple (user, auth)
            return (trader, payload)
        else:
            admin = _admin_repo.find_by_id(user_id)
            if not admin:
                raise AuthenticationFailed("Admin account not found.")

            if not admin.get("is_active", True):
                raise AuthenticationFailed("Admin account is deactivated.")

            # Attach structured admin info to the request for easy access in views
            request.admin = admin
            request.user = admin  # Sets DRF request.user
            return (admin, payload)

    def authenticate_header(self, request) -> str:
        return 'Bearer realm="ghana-tax-api"'

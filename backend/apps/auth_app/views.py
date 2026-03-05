"""
auth_app views — thin HTTP layer. All logic delegated to AuthService.
"""

import logging

from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.auth_app.serializers import (
    LoginSerializer,
    RefreshSerializer,
    CreateAdminSerializer,
    UpdateAdminSerializer,
)
from apps.auth_app.services import AuthService
from apps.auth_app.permissions import IsAdminAuthenticated, IsSysAdmin
from core.utils.response import success_response, error_response, created_response

logger = logging.getLogger(__name__)
_auth_service = AuthService()


# ── POST /api/auth/login ───────────────────────────────────────────────────────

@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation error.", errors=serializer.errors, http_status=400)

        try:
            result = _auth_service.login(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                ip_address=getattr(request, "client_ip", "unknown"),
                user_agent=getattr(request, "user_agent", ""),
            )
            return success_response(data=result, message="Login successful.")
        except Exception as exc:
            return error_response(str(exc), http_status=401)


# ── POST /api/auth/refresh ─────────────────────────────────────────────────────

@method_decorator(ratelimit(key="ip", rate="20/m", method="POST", block=True), name="post")
class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation error.", errors=serializer.errors, http_status=400)

        try:
            result = _auth_service.refresh_access_token(
                serializer.validated_data["refresh"]
            )
            return success_response(data=result, message="Token refreshed.")
        except Exception as exc:
            return error_response(str(exc), http_status=401)


# ── GET /api/me ────────────────────────────────────────────────────────────────

class MeView(APIView):
    permission_classes = [IsAdminAuthenticated]

    def get(self, request):
        admin = _auth_service.get_me(request.admin["admin_id"])
        if not admin:
            return error_response("Admin not found.", http_status=404)
        # Strip password_hash defensively
        admin.pop("password_hash", None)
        return success_response(data=admin)


# ── POST /api/admin/users ──────────────────────────────────────────────────────

class AdminUserListCreateView(APIView):
    permission_classes = [IsSysAdmin]

    def get(self, request):
        """GET /api/admin/users — list all admins."""
        admins = _auth_service.list_admins()
        return success_response(data=admins)

    def post(self, request):
        """POST /api/admin/users — create a new admin."""
        serializer = CreateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation error.", errors=serializer.errors, http_status=400)

        try:
            new_admin = _auth_service.create_admin(
                email=serializer.validated_data["email"],
                name=serializer.validated_data["name"],
                password=serializer.validated_data["password"],
                role=serializer.validated_data["role"],
                actor=request.admin,
                ip_address=getattr(request, "client_ip", "unknown"),
                user_agent=getattr(request, "user_agent", ""),
            )
            return created_response(data=new_admin, message="Admin created successfully.")
        except Exception as exc:
            return error_response(str(exc), http_status=400)


# ── PATCH /api/admin/users/{admin_id} ─────────────────────────────────────────

class AdminUserDetailView(APIView):
    permission_classes = [IsSysAdmin]

    def patch(self, request, admin_id: str):
        """PATCH /api/admin/users/{admin_id} — update role or is_active."""
        serializer = UpdateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation error.", errors=serializer.errors, http_status=400)

        try:
            updated = _auth_service.update_admin(
                target_admin_id=admin_id,
                updates=serializer.validated_data,
                actor=request.admin,
                ip_address=getattr(request, "client_ip", "unknown"),
                user_agent=getattr(request, "user_agent", ""),
            )
            return success_response(data=updated, message="Admin updated successfully.")
        except Exception as exc:
            status = 403 if "own role" in str(exc) else 400
            return error_response(str(exc), http_status=status)

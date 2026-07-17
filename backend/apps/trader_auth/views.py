import logging
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.trader_auth.serializers import (
    TraderOtpRequestSerializer,
    TraderOtpVerifySerializer,
    TraderRefreshSerializer,
)
from apps.trader_auth.services import TraderAuthService, RateLimitedError
from apps.ussd.validators import normalise_phone
from core.utils.response import success_response, error_response
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

_auth_service = TraderAuthService()

class TraderOtpRequestView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    @method_decorator(ratelimit(key="post:phone_number", rate="3/h", method="POST", block=True))
    def post(self, request):
        serializer = TraderOtpRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation failed. Please check your input.",
                errors=serializer.errors,
                http_status=400,
            )

        phone_number = normalise_phone(serializer.validated_data["phone_number"])
        request_info = {
            "ip_address": getattr(request, "client_ip", ""),
            "user_agent": getattr(request, "user_agent", ""),
        }

        try:
            message = _auth_service.request_otp(phone_number, request_info)
            return success_response(message=message)
        except RateLimitedError as e:
            return error_response(str(e), http_status=429)
        except Exception as e:
            logger.exception("OTP request failed")
            return error_response("Internal server error", http_status=500)

class TraderOtpVerifyView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True))
    @method_decorator(ratelimit(key="post:phone_number", rate="10/h", method="POST", block=True))
    def post(self, request):
        serializer = TraderOtpVerifySerializer(data=request.data)
        if not serializer.is_valid():
            # Must use errors= (not details=) — wrong kwarg caused TypeError → 500
            return error_response(
                "Validation failed. Please check your input.",
                errors=serializer.errors,
                http_status=400,
            )

        phone_number = normalise_phone(serializer.validated_data["phone_number"])
        # Canonical field is "code" (same as admin OTP verify); otp_code accepted as alias
        code = serializer.validated_data["code"]
        request_info = {
            "ip_address": getattr(request, "client_ip", ""),
            "user_agent": getattr(request, "user_agent", ""),
        }

        try:
            tokens, profile = _auth_service.verify_otp(phone_number, code, request_info)
            return success_response({**tokens, "trader": profile})
        except ValueError as e:
            return error_response(str(e), http_status=400)
        except Exception as e:
            logger.exception("OTP verify failed")
            return error_response("Internal server error", http_status=500)

class TraderRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @method_decorator(ratelimit(key="ip", rate="20/m", method="POST", block=True))
    def post(self, request):
        serializer = TraderRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation error.", errors=serializer.errors, http_status=400)

        try:
            result = _auth_service.refresh_access_token(
                serializer.validated_data["refresh"]
            )
            return success_response(data=result, message="Token refreshed.")
        except AuthenticationFailed as exc:
            return error_response(str(exc), http_status=401)
        except Exception as exc:
            logger.exception("Unexpected error during token refresh")
            return error_response("An internal error occurred.", http_status=500)

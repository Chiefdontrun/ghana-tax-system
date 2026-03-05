"""
Registration views — POST /api/register
"""

import logging

from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.permissions import AllowAny

from apps.registration.serializers import TraderRegistrationSerializer
from apps.registration.services import RegistrationService
from apps.tin.services import TINGenerationError
from core.utils.response import created_response, error_response

logger = logging.getLogger(__name__)

_registration_service = RegistrationService()


def _get_ip(request: Request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class RegisterTraderView(APIView):
    """
    POST /api/register
    Public endpoint — rate-limited to 20 req/min per IP.
    """

    permission_classes = [AllowAny]

    @ratelimit(key="ip", rate="20/m", method="POST", block=True)
    def post(self, request: Request):
        serializer = TraderRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation failed. Please check your input.",
                errors=serializer.errors,
                http_status=422,
            )

        ip = _get_ip(request)

        try:
            result = _registration_service.register_trader_web(
                validated_data=serializer.validated_data,
                ip_address=ip,
            )
        except TINGenerationError as exc:
            logger.error("TIN generation failed: %s", exc)
            return error_response(
                "Could not generate a TIN at this time. Please try again shortly.",
                http_status=503,
            )
        except Exception as exc:
            logger.exception("Unexpected registration error: %s", exc)
            return error_response(
                "An unexpected error occurred. Please try again.",
                http_status=500,
            )

        return created_response(data=result, message="Registration successful.")

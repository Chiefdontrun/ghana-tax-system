"""
TIN views — POST /api/tin/lookup
"""

import logging

from django_ratelimit.decorators import ratelimit
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.permissions import AllowAny

from apps.registration.validators import validate_ghana_phone
from apps.tin.serializers import TINLookupRequestSerializer
from apps.tin.services import TINService
from core.utils.response import error_response, success_response

logger = logging.getLogger(__name__)

_tin_service = TINService()


class TINLookupView(APIView):
    """
    POST /api/tin/lookup
    Public endpoint — rate-limited to 5 req/min per IP.
    """

    permission_classes = [AllowAny]

    @ratelimit(key="ip", rate="5/m", method="POST", block=True)
    def post(self, request: Request):
        serializer = TINLookupRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Invalid request data.", errors=serializer.errors)

        raw_phone: str = serializer.validated_data["phone_number"]

        try:
            phone = validate_ghana_phone(raw_phone)
        except Exception:
            return error_response(
                "Invalid phone number format. Use +233XXXXXXXXX or 0XXXXXXXXX.",
                http_status=422,
            )

        result = _tin_service.lookup_tin(phone)
        if result is None:
            return error_response(
                "No registration found for this phone number.",
                http_status=404,
            )

        return success_response(data=result, message="TIN found.")

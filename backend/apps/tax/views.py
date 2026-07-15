"""Tax views scaffold."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.utils.response import success_response


class TaxHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data={"status": "ok"}, message="Tax app ready.")

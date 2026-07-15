from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.auth_app.permissions import IsTraderAuthenticated
from apps.payments.serializers import InitiatePaymentSerializer
from apps.payments.services import PaymentService
from apps.payments.exceptions import PaymentInitiationError, PaymentNotFoundError


class PaymentInitiateView(APIView):
    permission_classes = [IsTraderAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        trader_id = request.user.get("trader_id")
        phone_number = request.user.get("phone_number")
        assessment_id = serializer.validated_data["assessment_id"]
        momo_network = serializer.validated_data["momo_network"]
        amount_pesewas = serializer.validated_data.get("amount_pesewas")

        payment_service = PaymentService()
        
        try:
            result = payment_service.initiate_payment(
                assessment_id=assessment_id,
                momo_network=momo_network,
                phone_number=phone_number,
                channel="web",
                actor_trader_id=trader_id,
                amount_pesewas=amount_pesewas
            )
            return Response(result, status=status.HTTP_201_CREATED)
            
        except PaymentNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PaymentInitiationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Let other unexpected errors bubble up to 500
            raise e


class PaymentStatusView(APIView):
    permission_classes = [IsTraderAuthenticated]

    def get(self, request, payment_id):
        trader_id = request.user.get("trader_id")
        payment_service = PaymentService()

        try:
            result = payment_service.get_payment_status(
                payment_id=payment_id,
                actor_trader_id=trader_id
            )
            return Response(result, status=status.HTTP_200_OK)
        except PaymentNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

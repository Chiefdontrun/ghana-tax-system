from rest_framework import serializers

class InitiatePaymentSerializer(serializers.Serializer):
    assessment_id = serializers.CharField(max_length=255)
    momo_network = serializers.ChoiceField(choices=["mtn", "telecel", "airteltigo"])
    amount_pesewas = serializers.IntegerField(required=False, min_value=1)
    phone_number = serializers.CharField(max_length=15, required=False)

class SubmitOtpSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=20)

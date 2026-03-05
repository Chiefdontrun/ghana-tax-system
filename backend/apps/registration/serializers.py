"""
Registration serializers — request/response shapes.
"""

from rest_framework import serializers

from apps.registration.validators import VALID_BUSINESS_TYPES, validate_ghana_phone


class LocationInputSerializer(serializers.Serializer):
    region = serializers.CharField(max_length=100)
    district = serializers.CharField(max_length=100)
    market_name = serializers.CharField(max_length=120)


class TraderRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=120)
    phone_number = serializers.CharField(max_length=20)
    business_type = serializers.ChoiceField(choices=VALID_BUSINESS_TYPES)
    location = LocationInputSerializer()

    def validate_phone_number(self, value: str) -> str:
        return validate_ghana_phone(value)


class RegistrationResponseSerializer(serializers.Serializer):
    tin_number = serializers.CharField()
    trader_id = serializers.CharField()
    name = serializers.CharField()
    sms_status = serializers.CharField()

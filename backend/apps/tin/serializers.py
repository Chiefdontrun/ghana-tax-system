"""
TIN serializers — request/response shapes for TIN endpoints.
"""

from rest_framework import serializers


class TINLookupRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)


class TINLookupResponseSerializer(serializers.Serializer):
    tin_number = serializers.CharField()
    name_masked = serializers.CharField()
    status = serializers.CharField()

from rest_framework import serializers

class TraderOtpRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

class TraderOtpVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, min_length=6)

class TraderRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

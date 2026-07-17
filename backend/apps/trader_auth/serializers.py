"""Trader auth serializers — field names aligned with admin OTP (`code`)."""

import re

from rest_framework import serializers


class TraderOtpRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)


class TraderOtpVerifySerializer(serializers.Serializer):
    """
    Canonical body: { "phone_number": "...", "code": "123456" }
    Matches admin VerifyOtpSerializer field name `code` and the trader frontend.
    Optional alias `otp_code` accepted for backward compatibility.
    """

    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, min_length=6, required=False, allow_blank=True)
    otp_code = serializers.CharField(max_length=6, min_length=6, required=False, allow_blank=True)

    def validate(self, attrs):
        code = (attrs.get("code") or attrs.get("otp_code") or "").strip()
        if not code:
            raise serializers.ValidationError(
                {"code": "This field is required. Send a 6-digit OTP as 'code'."}
            )
        if not re.fullmatch(r"\d{6}", code):
            raise serializers.ValidationError(
                {"code": "Must be a 6-digit numeric verification code."}
            )
        attrs["code"] = code
        return attrs


class TraderRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

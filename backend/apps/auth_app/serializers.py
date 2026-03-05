"""
auth_app serializers — input validation for auth endpoints.
"""

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=1, write_only=True, trim_whitespace=False)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(min_length=1)


class CreateAdminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(min_length=2, max_length=120)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    role = serializers.ChoiceField(choices=["SYS_ADMIN", "TAX_ADMIN"])


class UpdateAdminSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["SYS_ADMIN", "TAX_ADMIN"], required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one of 'role' or 'is_active' must be provided.")
        return attrs

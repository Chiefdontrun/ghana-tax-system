"""
Reports serializers — query param parsing and response shapes.
"""

from rest_framework import serializers


# ── Query param serializers ───────────────────────────────────────────────────

VALID_PERIODS = ["7d", "30d", "all"]


class ReportsSummaryQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=VALID_PERIODS, default="30d")


class ReportsExportQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=VALID_PERIODS, required=False)
    channel = serializers.ChoiceField(
        choices=["web", "ussd"], required=False, allow_blank=True
    )
    business_type = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)


class TradersListQuerySerializer(serializers.Serializer):
    channel = serializers.ChoiceField(
        choices=["web", "ussd"], required=False, allow_blank=True
    )
    business_type = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)

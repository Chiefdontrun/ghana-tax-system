from rest_framework import serializers

class InitiatePaymentSerializer(serializers.Serializer):
    assessment_id = serializers.CharField(max_length=100)
    amount_pesewas = serializers.IntegerField(required=False, min_value=1)
    momo_network = serializers.ChoiceField(choices=["mtn", "telecel", "airteltigo"])

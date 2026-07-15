import pytest
from rest_framework import status
from django.urls import reverse

@pytest.mark.django_db
def test_debug(client, trader_headers, setup_data):
    url = reverse("payment-initiate")
    payload = {
        "assessment_id": setup_data["assessment_id"],
        "amount_pesewas": 2000,
        "momo_network": "mtn"
    }
    response = client.post(url, payload, content_type="application/json", **trader_headers)
    print("DEBUG RESPONSE:")
    print(response.json())

import json
import pytest
from django.urls import reverse

ARKESEL_PAYLOAD = {
  "sessionID": "17841458811439225",
  "userID": "3NV5OX7PZK_HICOs",
  "newSession": True,
  "msisdn": "233231804643",
  "userData": "*928*309#",
  "network": "MTN"
}

@pytest.mark.django_db
def test_arkesel_initial_dial(client):
    resp = client.post(
        "/ussd/callback/",
        data=json.dumps(ARKESEL_PAYLOAD),
        content_type="application/json"
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["sessionID"] == "17841458811439225"
    assert data["userID"] == "3NV5OX7PZK_HICOs"
    assert data["msisdn"] == "233231804643"
    assert data["continueSession"] is True
    assert "Register Business" in data["message"]

@pytest.mark.django_db
def test_arkesel_subsequent_dial(client):
    # Mocking that the user selected "1" (Register)
    payload = ARKESEL_PAYLOAD.copy()
    payload["newSession"] = False
    payload["userData"] = "1"
    
    # Needs a session from previous dial to hit Step 1, so we simulate the initial dial first
    client.post("/ussd/callback/", data=json.dumps(ARKESEL_PAYLOAD), content_type="application/json")
    
    resp = client.post(
        "/ussd/callback/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["continueSession"] is True
    assert "full name" in data["message"].lower()


"""Phase F2 boundary: rate-schedule mutations are SYS_ADMIN only."""

import json
import uuid
from datetime import datetime, timezone

import pytest


@pytest.mark.django_db
def test_tax_admin_cannot_create_rate_schedule(auth_client_tax):
    resp = auth_client_tax.post(
        "/api/tax/rate-schedules/",
        data=json.dumps({
            "tax_category": "BOP",
            "business_type": "food_vendor",
            "rate_type": "FIXED",
            "fixed_amount": 5000,
            "effective_year": 2026,
        }),
        content_type="application/json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_sys_admin_can_create_rate_schedule(auth_client_sys, test_db):
    resp = auth_client_sys.post(
        "/api/tax/rate-schedules/",
        data=json.dumps({
            "tax_category": "BOP",
            "business_type": "food_vendor",
            "rate_type": "FIXED",
            "fixed_amount": 5000,
            "effective_year": 2026,
            "is_active": True,
        }),
        content_type="application/json",
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["schedule_id"]
    assert test_db["tax_rate_schedules"].count_documents({}) == 1


@pytest.mark.django_db
def test_tax_admin_cannot_patch_rate_schedule(auth_client_tax, test_db):
    sid = str(uuid.uuid4())
    test_db["tax_rate_schedules"].insert_one({
        "schedule_id": sid,
        "tax_category": "BOP",
        "business_type": "food_vendor",
        "rate_type": "FIXED",
        "fixed_amount": 1000,
        "effective_year": 2026,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    })
    resp = auth_client_tax.patch(
        f"/api/tax/rate-schedules/{sid}/",
        data=json.dumps({"is_active": False}),
        content_type="application/json",
    )
    assert resp.status_code == 403

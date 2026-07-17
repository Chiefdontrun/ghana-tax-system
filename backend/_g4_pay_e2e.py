"""G4 payment E2E helper — plant OTP, login, Paystack sandbox charge."""
import json
import os
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

import bcrypt
from decouple import Config, RepositoryEnv

env = Config(RepositoryEnv(str(Path(__file__).parent / ".env")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django

django.setup()

from core.utils.mongo import get_db, get_collection, TAX_ASSESSMENTS, TAX_PAYMENTS

API = "https://ghana-tax-system-hh6f.vercel.app"
phone = "+233246991337"
trader_id = "47510678-3d1d-4b94-87e4-2d3eae605725"
assessment_id = "310d4cb7-ae73-49ae-849d-879f0226e254"
code = "482917"


def post(path, data=None, headers=None):
    body = None if data is None else json.dumps(data).encode()
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(API + path, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            j = json.loads(raw or "{}")
        except Exception:
            j = {"raw": raw[:400]}
        return e.code, j


def get(path, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(API + path, headers=h, method="GET")
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            j = json.loads(raw or "{}")
        except Exception:
            j = {"raw": raw[:400]}
        return e.code, j


def main():
    hashed = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
    db = get_db()
    now = datetime.now(timezone.utc)
    db["trader_otp_verifications"].update_many(
        {"phone_number": phone, "used_at": None, "invalidated_at": None},
        {"$set": {"invalidated_at": now}},
    )
    otp_id = str(uuid.uuid4())
    db["trader_otp_verifications"].insert_one(
        {
            "otp_id": otp_id,
            "trader_id": trader_id,
            "phone_number": phone,
            "otp_hash": hashed,
            "expires_at": now + timedelta(minutes=10),
            "attempts": 0,
            "resend_count": 0,
            "created_at": now,
            "used_at": None,
            "invalidated_at": None,
        }
    )
    print("INSERTED_OTP", otp_id)

    st, body = post(
        "/api/trader-auth/verify-otp/",
        {"phone_number": phone, "otp_code": code},
    )
    print("VERIFY", st, str(body)[:400])
    data = body.get("data") or body
    tok = data.get("access_token") or data.get("access")
    if not tok:
        # serializer may use different field
        st, body = post(
            "/api/trader-auth/verify-otp/",
            {"phone_number": phone, "code": code},
        )
        print("VERIFY2", st, str(body)[:400])
        data = body.get("data") or body
        tok = data.get("access_token") or data.get("access")
    if not tok:
        print("NO TOKEN")
        return

    print("GOT_TOKEN")
    st, biz = get("/api/my-businesses/", {"Authorization": f"Bearer {tok}"})
    print("MY_BIZ", st, str(biz)[:400])

    st, pay = post(
        "/api/tax/payments/initiate/",
        {
            "assessment_id": assessment_id,
            "momo_network": "mtn",
            "phone_number": "0551234987",
            "amount_pesewas": 75000,
        },
        {"Authorization": f"Bearer {tok}"},
    )
    print("PAY", st, str(pay)[:600])
    pid = pay.get("payment_id") or (pay.get("data") or {}).get("payment_id")
    if not pid and isinstance(pay, dict):
        # unwrap nested
        for k in ("data", "payment"):
            if isinstance(pay.get(k), dict) and pay[k].get("payment_id"):
                pid = pay[k]["payment_id"]
    if pid:
        for i in range(10):
            time.sleep(3)
            st2, ps = get(
                f"/api/tax/payments/{pid}/status/",
                {"Authorization": f"Bearer {tok}"},
            )
            print("PS", i, st2, str(ps)[:350])
            status = (ps.get("status") or (ps.get("data") or {}).get("status") or "")
            if str(status).upper() in ("SUCCESS", "PAID", "FAILED"):
                break
            # submit otp if required
            if ps.get("requires_otp") or (ps.get("data") or {}).get("requires_otp"):
                st3, otpr = post(
                    f"/api/tax/payments/{pid}/submit-otp/",
                    {"otp": "123456"},
                    {"Authorization": f"Bearer {tok}"},
                )
                print("SUBMIT_OTP", st3, str(otpr)[:300])

    a = get_collection(TAX_ASSESSMENTS).find_one(
        {"assessment_id": assessment_id},
        {"_id": 0, "status": 1, "amount_paid": 1, "amount_due": 1},
    )
    pays = list(
        get_collection(TAX_PAYMENTS).find(
            {"assessment_id": assessment_id},
            {"_id": 0, "payment_id": 1, "status": 1, "amount_pesewas": 1, "channel": 1},
        )
    )
    print("ASSESS", a)
    print("PAYS", pays)


if __name__ == "__main__":
    main()

"""
conftest.py — shared pytest fixtures for all backend tests.

Design decisions:
- Each test gets a fresh isolated MongoDB database (unique name per session).
- MongoClient singleton is reset between test modules so fixture DB is used.
- Django test client used for view-level tests.
- Factory fixtures build minimal valid documents without hitting real providers.
"""

import sys
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import bcrypt
import pytest

from django.test import Client as DjangoClient

# Python 3.14 + Django 4.2: BaseContext.__copy__ uses super().__copy__() then
# sets .dicts, which raises AttributeError on 3.14 during error-template render
# in the test client. Patch only on 3.14+; production should use Python 3.12
# (see backend/runtime.txt).
if sys.version_info >= (3, 14):
    try:
        from django.template.context import BaseContext

        def _base_context_copy(self):
            duplicate = object.__new__(type(self))
            duplicate.__dict__ = self.__dict__.copy()
            duplicate.dicts = self.dicts[:]
            return duplicate

        BaseContext.__copy__ = _base_context_copy  # type: ignore[method-assign]
    except Exception:
        pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Database fixture ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_db_name():
    """Unique DB name per test session so parallel runs don't collide."""
    return f"ghana_tax_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def mongo_uri():
    """
    Prefer local Mongo (docker-compose.dev.yml). If unreachable, fall back to
    MONGO_URI from the environment / .env (typically Atlas) so the suite can
    still exercise real request→session-store→state-machine paths.
    Uses a unique test database name — never writes into the production DB name.
    """
    from pymongo import MongoClient

    local = "mongodb://localhost:27017"
    try:
        c = MongoClient(local, serverSelectionTimeoutMS=2000)
        c.admin.command("ping")
        c.close()
        return local
    except Exception:
        pass

    try:
        from decouple import config
        remote = config("MONGO_URI", default="")
    except Exception:
        remote = ""
    if not remote:
        import os
        remote = os.environ.get("MONGO_URI", "")
    if not remote:
        pytest.skip("No MongoDB: start docker-compose (infra/) or set MONGO_URI")

    # Atlas URIs often embed a default DB path; client still allows other DB names.
    c = MongoClient(remote, serverSelectionTimeoutMS=15000)
    c.admin.command("ping")
    c.close()
    return remote


@pytest.fixture(scope="session")
def mongo_client(test_db_name, mongo_uri):
    """
    Real MongoClient pointed at a fresh test database.
    Drops the database after the entire session.
    """
    from pymongo import MongoClient
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=15000)
    yield client
    # Prefer dropDatabase; Atlas free/shared users may lack dropDatabase —
    # fall back to deleting all collections so we never leave junk forever.
    try:
        client.drop_database(test_db_name)
    except Exception:
        try:
            db = client[test_db_name]
            for name in db.list_collection_names():
                db.drop_collection(name)
        except Exception:
            pass
    finally:
        client.close()


@pytest.fixture(autouse=True)
def test_db(mongo_client, test_db_name, mongo_uri, settings):
    """
    Per-test fixture:
    - Points Django settings at the test DB.
    - Resets the PyMongo singleton so all repositories use test_db.
    - Clears all collections before each test (clean slate).
    - Flushes Redis USSD session keys between tests.
    """
    settings.MONGO_DB_NAME = test_db_name
    settings.MONGO_URI = mongo_uri

    # Point PyMongo singleton directly at the test DB
    import core.utils.mongo as mongo_module
    mongo_module._client = mongo_client
    mongo_module._db = mongo_client[test_db_name]

    db = mongo_client[test_db_name]
    for col in ["traders", "businesses", "locations", "admins", "audit_logs", "ussd_sessions", "otp_verifications", "tax_rate_schedules", "tax_assessments", "tax_payments", "tax_assessment_exceptions", "trader_otp_verifications"]:
        db[col].delete_many({})

    # Clear Redis USSD sessions between tests atomically
    try:
        import redis as redis_lib
        r = redis_lib.from_url("redis://localhost:6379/0", decode_responses=True, socket_timeout=2)
        r.ping()
        # Use flushdb for atomic, guaranteed full clearance of all test session data
        r.flushdb()
    except Exception:
        pass  # Redis not available — MongoDB fallback used

    # Isolate reports Redis/LocMem cache between tests (cache keys are not DB-scoped)
    try:
        from django.core.cache import cache
        cache.clear()
    except Exception:
        pass

    yield db


# ── Admin fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sys_admin_doc(test_db):
    admin_id = str(uuid.uuid4())
    doc = {
        "admin_id": admin_id,
        "email": "sysadmin@test.gov.gh",
        "name": "System Admin",
        "role": "SYS_ADMIN",
        "password_hash": _hash("TestPass123!"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "last_login_at": None,
    }
    test_db["admins"].insert_one(doc)
    return doc


@pytest.fixture
def tax_admin_doc(test_db):
    admin_id = str(uuid.uuid4())
    doc = {
        "admin_id": admin_id,
        "email": "taxadmin@test.gov.gh",
        "name": "Tax Admin",
        "role": "TAX_ADMIN",
        "password_hash": _hash("TestPass123!"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "last_login_at": None,
    }
    test_db["admins"].insert_one(doc)
    return doc


@pytest.fixture
def sys_admin_token(sys_admin_doc):
    from apps.auth_app.jwt_utils import generate_access_token
    return generate_access_token(sys_admin_doc["admin_id"], "SYS_ADMIN")


@pytest.fixture
def tax_admin_token(tax_admin_doc):
    from apps.auth_app.jwt_utils import generate_access_token
    return generate_access_token(tax_admin_doc["admin_id"], "TAX_ADMIN")


# ── Trader / business factory fixture ─────────────────────────────────────────

@pytest.fixture
def sample_trader(test_db):
    """
    Insert one trader + matching business document.
    Returns the trader dict.
    """
    trader_id = str(uuid.uuid4())
    tin = f"GH-TIN-{uuid.uuid4().hex[:6].upper()}"
    trader = {
        "trader_id": trader_id,
        "tin_number": tin,
        "name": "Kofi Mensah",
        "phone_number": "+233244000001",
        "business_type": "food_vendor",
        "region": "Greater Accra",
        "district": "Accra Central",
        "market_name": "Makola Market",
        "channel": "web",
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    test_db["traders"].insert_one(trader)
    test_db["businesses"].insert_one({
        "business_id": str(uuid.uuid4()),
        "owner_trader_id": trader_id,
        "business_type": "food_vendor",
        "tin_number": tin,
        "created_at": datetime.now(timezone.utc),
    })
    trader.pop("_id", None)
    return trader


# ── Django test client ────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return DjangoClient()


@pytest.fixture
def auth_client_tax(tax_admin_token):
    c = DjangoClient()
    c.defaults["HTTP_AUTHORIZATION"] = f"Bearer {tax_admin_token}"
    return c


@pytest.fixture
def auth_client_sys(sys_admin_token):
    c = DjangoClient()
    c.defaults["HTTP_AUTHORIZATION"] = f"Bearer {sys_admin_token}"
    return c


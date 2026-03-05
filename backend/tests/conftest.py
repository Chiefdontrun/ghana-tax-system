"""
conftest.py — shared pytest fixtures for all backend tests.

Design decisions:
- Each test gets a fresh isolated MongoDB database (unique name per session).
- MongoClient singleton is reset between test modules so fixture DB is used.
- Django test client used for view-level tests.
- Factory fixtures build minimal valid documents without hitting real providers.
"""

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import bcrypt
import pytest

from django.test import Client as DjangoClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Database fixture ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_db_name():
    """Unique DB name per test session so parallel runs don't collide."""
    return f"ghana_tax_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def mongo_client(test_db_name):
    """
    Real MongoClient pointed at a fresh test database.
    Drops the database after the entire session.
    """
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
    yield client
    client.drop_database(test_db_name)
    client.close()


@pytest.fixture(autouse=True)
def test_db(mongo_client, test_db_name, settings):
    """
    Per-test fixture:
    - Points Django settings at the test DB.
    - Resets the PyMongo singleton so all repositories use test_db.
    - Clears all collections before each test (clean slate).
    - Flushes Redis USSD session keys between tests.
    """
    settings.MONGO_DB_NAME = test_db_name
    settings.MONGO_URI = "mongodb://localhost:27017"

    # Point PyMongo singleton directly at the test DB
    import core.utils.mongo as mongo_module
    mongo_module._client = mongo_client
    mongo_module._db = mongo_client[test_db_name]

    db = mongo_client[test_db_name]
    for col in ["traders", "businesses", "locations", "admins", "audit_logs", "ussd_sessions"]:
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

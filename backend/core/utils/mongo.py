"""
PyMongo connection singleton for ghana-tax-system.
Provides a single MongoClient shared across the entire Django process,
with retry-on-startup logic and a clean get_db() / get_collection() API.
"""

import logging
import time
import re
from typing import Optional

from django.conf import settings
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# ── Collection name constants ─────────────────────────────────────────────────
TRADERS = "traders"
BUSINESSES = "businesses"
LOCATIONS = "locations"
ADMINS = "admins"
AUDIT_LOGS = "audit_logs"
USSD_SESSIONS = "ussd_sessions"
OTP_VERIFICATIONS = "otp_verifications"
TAX_RATE_SCHEDULES = "tax_rate_schedules"
TAX_ASSESSMENTS = "tax_assessments"
TAX_PAYMENTS = "tax_payments"

# ── Singleton holders ─────────────────────────────────────────────────────────
_client: Optional[MongoClient] = None
_db: Optional[Database] = None

_MAX_RETRIES = 1
_RETRY_DELAY_S = 0


def get_client() -> MongoClient:
    """
    Return the singleton MongoClient, creating it on first call.
    Retries up to _MAX_RETRIES times with _RETRY_DELAY_S delay between attempts.
    Raises RuntimeError if all retries are exhausted.
    """
    global _client

    if _client is not None:
        return _client

    uri = settings.MONGO_URI
    last_exc: Exception = RuntimeError("Unknown error initialising MongoDB client")

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=5000,
            )
            # Trigger an actual network round-trip to verify connectivity
            client.admin.command("ping")
            _client = client
            # Log only the host and database name — never log credentials
            m = re.match(r'^(?:mongodb(?:\+srv)?://)(?:[^@]+@)?(?P<host>[^/]+)(?:/(?P<db>[^?]+))?', uri)
            if m:
                host = m.group('host')
                db_name = m.group('db') or settings.MONGO_DB_NAME
            else:
                host = uri
                db_name = settings.MONGO_DB_NAME

            logger.info(
                "MongoDB connected (attempt %d/%d): %s/%s",
                attempt,
                _MAX_RETRIES,
                host,
                db_name,
            )
            return _client
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            last_exc = exc
            logger.warning(
                "MongoDB connection attempt %d/%d failed: %s — retrying in %ds",
                attempt,
                _MAX_RETRIES,
                exc,
                _RETRY_DELAY_S,
            )
            if attempt < _MAX_RETRIES and _RETRY_DELAY_S:
                time.sleep(_RETRY_DELAY_S)

    raise RuntimeError(
        f"Could not connect to MongoDB after {_MAX_RETRIES} attempts. "
        f"Last error: {last_exc}"
    ) from last_exc


def get_db() -> Database:
    """Return the primary database instance."""
    global _db
    if _db is None:
        _db = get_client()[settings.MONGO_DB_NAME]
    return _db


def get_collection(name: str):
    """Convenience helper — returns a named collection from the primary database."""
    return get_db()[name]


def close_client() -> None:
    """Close the MongoClient (call during teardown / tests)."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB client closed.")

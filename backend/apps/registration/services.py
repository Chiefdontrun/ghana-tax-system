"""
RegistrationService — orchestrates trader registration for web and USSD channels.
"""

import logging
import uuid
from datetime import datetime, timezone

from apps.audit.repository import AuditRepository
from apps.registration.repository import (
    BusinessRepository,
    LocationRepository,
    TraderRepository,
)
from apps.ussd.validators import normalise_phone
from apps.tin.services import TINService

logger = logging.getLogger(__name__)

_trader_repo = TraderRepository()
_business_repo = BusinessRepository()
_location_repo = LocationRepository()
_audit_repo = AuditRepository()
_tin_service = TINService()


class RegistrationService:
    """All trader registration business logic lives here, not in views."""

    def register_trader_web(self, validated_data: dict, ip_address: str) -> dict:
        """
        Full registration pipeline for web channel:
        1. Idempotency — return existing TIN if phone already registered.
        2. Find-or-create location.
        3. Generate unique TIN.
        4. Create trader + business documents.
        5. Write CREATE_TRADER audit log.
        6. Stub SMS notification.
        Returns {tin_number, trader_id, name, sms_status}.
        """
        phone: str = normalise_phone(validated_data["phone_number"])
        name: str = validated_data["name"]
        business_type: str = validated_data["business_type"]
        loc: dict = validated_data["location"]

        # ── 1. Idempotency ────────────────────────────────────────────────────
        existing = _trader_repo.find_by_phone(phone)
        if existing:
            logger.info("Idempotent registration for phone %s — returning existing TIN.", phone)
            return {
                "tin_number": existing["tin_number"],
                "trader_id": existing["trader_id"],
                "name": existing["name"],
                "sms_status": "skipped",
            }

        # ── 2. Location ───────────────────────────────────────────────────────
        location = _location_repo.find_or_create(
            region=loc["region"],
            district=loc["district"],
            market_name=loc["market_name"],
        )

        # ── 3. Generate TIN ───────────────────────────────────────────────────
        tin_number = _tin_service.generate_unique_tin()
        trader_id = str(uuid.uuid4())

        # ── 4a. Create trader ─────────────────────────────────────────────────
        trader_doc = {
            "trader_id": trader_id,
            "tin_number": tin_number,
            "name": name,
            "phone_number": phone,
            "business_type": business_type,
            "region": location.get("region", loc["region"]),
            "district": location.get("district", loc["district"]),
            "market_name": location.get("market_name", loc["market_name"]),
            "location_id": location.get("location_id"),
            "channel": "web",
            "status": "active",
            "ip_address": ip_address,
        }
        _trader_repo.create(trader_doc)

        # ── 4b. Create business ───────────────────────────────────────────────
        business_doc = {
            "business_id": str(uuid.uuid4()),
            "owner_trader_id": trader_id,
            "business_type": business_type,
            "tin_number": tin_number,
            "location_id": location.get("location_id"),
        }
        _business_repo.create(business_doc)

        # ── 5. Audit log ──────────────────────────────────────────────────────
        _audit_repo.log({
            "action": "CREATE_TRADER",
            "entity_type": "trader",
            "entity_id": trader_id,
            "actor_type": "system",
            "channel": "web",
            "details": {
                "tin_number": tin_number,
                "name": name,
                "phone_number": phone,
                "business_type": business_type,
                "ip_address": ip_address,
            },
        })

        # ── 6. SMS stub ───────────────────────────────────────────────────────
        sms_status = self._send_tin_sms_stub(phone, tin_number, name)

        return {
            "tin_number": tin_number,
            "trader_id": trader_id,
            "name": name,
            "sms_status": sms_status,
        }

    def register_trader_ussd(self, collected: dict, msisdn: str) -> dict:
        """
        USSD registration pipeline — called from the USSD state machine.
        Uses register_trader_web internally with USSD channel override.
        """
        validated = {
            "name": collected.get("name", ""),
            "phone_number": normalise_phone(msisdn),
            "business_type": collected.get("business_type", "other"),
            "location": {
                "region": collected.get("region", "Unknown"),
                "district": collected.get("market_name", "Unknown"),
                "market_name": collected.get("market_name", "Unknown"),
            },
        }

        # ── Idempotency ───────────────────────────────────────────────────────
        existing = _trader_repo.find_by_phone(normalise_phone(msisdn))
        if existing:
            return {
                "tin_number": existing["tin_number"],
                "trader_id": existing["trader_id"],
                "name": existing["name"],
                "sms_status": "skipped",
            }

        loc = validated["location"]
        location = _location_repo.find_or_create(
            region=loc["region"],
            district=loc["district"],
            market_name=loc["market_name"],
        )

        tin_number = _tin_service.generate_unique_tin()
        trader_id = str(uuid.uuid4())

        trader_doc = {
            "trader_id": trader_id,
            "tin_number": tin_number,
            "name": validated["name"],
            "phone_number": msisdn,
            "business_type": validated["business_type"],
            "region": location.get("region", loc["region"]),
            "district": location.get("district", loc["district"]),
            "market_name": location.get("market_name", loc["market_name"]),
            "location_id": location.get("location_id"),
            "channel": "ussd",
            "status": "active",
        }
        _trader_repo.create(trader_doc)

        business_doc = {
            "business_id": str(uuid.uuid4()),
            "owner_trader_id": trader_id,
            "business_type": validated["business_type"],
            "tin_number": tin_number,
            "location_id": location.get("location_id"),
        }
        _business_repo.create(business_doc)

        _audit_repo.log({
            "action": "CREATE_TRADER",
            "entity_type": "trader",
            "entity_id": trader_id,
            "actor_type": "system",
            "channel": "ussd",
            "details": {
                "tin_number": tin_number,
                "name": validated["name"],
                "phone_number": msisdn,
                "business_type": validated["business_type"],
            },
        })

        sms_status = self._send_tin_sms_stub(msisdn, tin_number, validated["name"])
        return {
            "tin_number": tin_number,
            "trader_id": trader_id,
            "name": validated["name"],
            "sms_status": sms_status,
        }

    @staticmethod
    def _send_tin_sms_stub(phone: str, tin_number: str, name: str) -> str:
        """
        Delegate to NotificationService (wired in Phase 7).
        Returns 'sent' on success, 'failed' on provider error.
        """
        try:
            from apps.notifications.services import NotificationService
            result = NotificationService().send_tin_sms(phone, tin_number, name)
            return "sent" if result.get("success") else "failed"
        except Exception as exc:
            logger.warning("SMS notification error for %s: %s", phone, exc)
            return "failed"

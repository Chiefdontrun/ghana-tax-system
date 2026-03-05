"""
TINService — TIN generation and lookup logic.
"""

import logging
import secrets

from apps.audit.repository import AuditRepository
from apps.registration.repository import TraderRepository
from apps.tin.repository import TINRepository

logger = logging.getLogger(__name__)

audit_repo = AuditRepository()
tin_repo = TINRepository()
trader_repo = TraderRepository()


class TINGenerationError(Exception):
    """Raised when a unique TIN cannot be generated after MAX_RETRIES attempts."""


class TINService:
    TIN_PREFIX = "GH-TIN-"
    MAX_RETRIES = 10

    def generate_unique_tin(self) -> str:
        """
        Generate a cryptographically random, unique TIN.
        Format: GH-TIN-XXXXXX (6 uppercase hex chars).
        Retries up to MAX_RETRIES if a collision is detected.
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            suffix = secrets.token_hex(3).upper()  # 6-char hex string
            tin = f"{self.TIN_PREFIX}{suffix}"
            if not tin_repo.exists(tin):
                logger.debug("Generated TIN %s on attempt %d", tin, attempt)
                return tin
            logger.warning("TIN collision on attempt %d: %s", attempt, tin)

        # All retries exhausted — write audit log and raise
        audit_repo.log({
            "action": "TIN_GENERATION_FAILED",
            "entity_type": "tin",
            "details": {"max_retries": self.MAX_RETRIES},
            "channel": "system",
        })
        raise TINGenerationError(
            f"Could not generate a unique TIN after {self.MAX_RETRIES} attempts."
        )

    def lookup_tin(self, phone_number: str) -> dict | None:
        """
        Find a trader by normalised phone number.
        Returns {tin_number, name_masked, status} or None.
        Name mask: first 2 chars + *** + last char  (e.g., "Jo***e").
        """
        trader = trader_repo.find_by_phone(phone_number)
        if not trader:
            return None

        name: str = trader.get("name", "")
        if len(name) >= 3:
            masked_name = name[:2] + "***" + name[-1]
        elif len(name) == 2:
            masked_name = name[0] + "***"
        else:
            masked_name = "***"

        return {
            "tin_number": trader.get("tin_number"),
            "name_masked": masked_name,
            "status": trader.get("status", "active"),
        }

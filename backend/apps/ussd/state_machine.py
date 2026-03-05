"""
USSD State Machine for the Ghana District Assembly Revenue System.
Compatible with Africa's Talking USSD webhook format.

Flow overview:
  MAIN_MENU
    → "1" → REG_NAME → REG_BUSINESS_TYPE → REG_REGION
              → REG_DISTRICT → REG_CONFIRM → COMPLETE
    → "2" → CHECK_TIN → END
    → "3" → HELP → END
"""

import logging

from apps.audit.repository import AuditRepository
from apps.registration.services import RegistrationService
from apps.tin.services import TINService, TINGenerationError
from apps.ussd.session_store import USSDSessionStore
from apps.ussd.validators import (
    normalise_phone,
    validate_ussd_market,
    validate_ussd_name,
    validate_ussd_phone,
)

logger = logging.getLogger(__name__)

# ── State constants ────────────────────────────────────────────────────────────
STATE_MAIN_MENU = "MAIN_MENU"
STATE_REG_NAME = "REG_NAME"
STATE_REG_BUSINESS_TYPE = "REG_BUSINESS_TYPE"
STATE_REG_REGION = "REG_REGION"
STATE_REG_DISTRICT = "REG_DISTRICT"
STATE_REG_CONFIRM = "REG_CONFIRM"
STATE_CHECK_TIN = "CHECK_TIN"
STATE_HELP = "HELP"
STATE_COMPLETE = "COMPLETE"

# ── Display mappings ───────────────────────────────────────────────────────────
BUSINESS_TYPE_MAP = {
    "1": "food_vendor",
    "2": "clothing",
    "3": "electronics",
    "4": "services",
    "5": "agriculture",
    "6": "other",
}

BUSINESS_TYPE_LABELS = {
    "food_vendor": "Food Vendor",
    "clothing": "Clothing",
    "electronics": "Electronics",
    "services": "Services",
    "agriculture": "Agriculture",
    "other": "Other",
}

REGION_MAP = {
    "1": "Greater Accra",
    "2": "Ashanti",
    "3": "Western",
    "4": "Northern",
    "5": "Eastern",
    "6": "Volta",
    "7": "Other",
}

# ── Singletons ─────────────────────────────────────────────────────────────────
_session_store = USSDSessionStore()
_registration_service = RegistrationService()
_tin_service = TINService()
_audit_repo = AuditRepository()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _main_menu_text() -> str:
    return (
        "CON Welcome to DA Revenue\n"
        "1. Register Business\n"
        "2. Check My TIN\n"
        "3. Help"
    )


def _new_session(msisdn: str) -> dict:
    return {
        "step": STATE_MAIN_MENU,
        "phone_number": msisdn,
        "collected": {},
    }


# ── State Machine ──────────────────────────────────────────────────────────────

class USSDStateMachine:
    """
    Processes a single USSD webhook call and returns a plain-text response.
    Africa's Talking passes the full `text` field as a `*`-delimited history
    string (e.g., "1*Kofi Mensah*2"). We parse only the LAST segment as the
    current user input and restore all other state from the session store.
    """

    def process(
        self,
        session_id: str,
        msisdn: str,
        text: str,
    ) -> str:
        """
        Main entry point. Returns a string starting with either:
          "CON ..." — expects further input
          "END ..." — terminates the session
        """
        # Parse the most recent user input from the `*`-delimited history
        parts = text.split("*") if text else []
        user_input = parts[-1].strip() if parts else ""
        is_initial = (text == "" or text is None)

        # Load or create session
        session = _session_store.get(session_id)
        if session is None or is_initial:
            session = _new_session(msisdn)

        current_step = session.get("step", STATE_MAIN_MENU)

        # Write step audit
        _audit_repo.log({
            "action": "USSD_SESSION_STEP",
            "entity_type": "ussd_session",
            "entity_id": session_id,
            "actor_type": "trader",
            "channel": "ussd",
            "details": {
                "step": current_step,
                "msisdn": msisdn,
                "input_length": len(user_input),
            },
        })

        # Route to the correct handler
        response = self._route(session, session_id, msisdn, user_input, is_initial)
        return response

    # ── Router ─────────────────────────────────────────────────────────────────

    def _route(
        self,
        session: dict,
        session_id: str,
        msisdn: str,
        user_input: str,
        is_initial: bool,
    ) -> str:
        step = session["step"]

        if is_initial or step == STATE_MAIN_MENU:
            return self._handle_main_menu(session, session_id, msisdn, user_input, is_initial)
        elif step == STATE_REG_NAME:
            return self._handle_reg_name(session, session_id, user_input)
        elif step == STATE_REG_BUSINESS_TYPE:
            return self._handle_reg_business_type(session, session_id, user_input)
        elif step == STATE_REG_REGION:
            return self._handle_reg_region(session, session_id, user_input)
        elif step == STATE_REG_DISTRICT:
            return self._handle_reg_district(session, session_id, user_input)
        elif step == STATE_REG_CONFIRM:
            return self._handle_reg_confirm(session, session_id, msisdn, user_input)
        elif step == STATE_CHECK_TIN:
            return self._handle_check_tin(session, session_id, msisdn, user_input)
        elif step == STATE_HELP:
            # Should never reach here — HELP goes straight to END
            return self._end_help()
        else:
            # Unknown state — reset
            _session_store.delete(session_id)
            return _main_menu_text()

    # ── Handlers ───────────────────────────────────────────────────────────────

    def _handle_main_menu(
        self,
        session: dict,
        session_id: str,
        msisdn: str,
        user_input: str,
        is_initial: bool,
    ) -> str:
        if is_initial or user_input == "":
            # First dial — show menu, persist session at MAIN_MENU
            session["step"] = STATE_MAIN_MENU
            _session_store.set(session_id, session)
            return _main_menu_text()

        if user_input == "1":
            session["step"] = STATE_REG_NAME
            _session_store.set(session_id, session)
            return (
                "CON Step 1 of 5\n"
                "Enter your full name:"
            )
        elif user_input == "2":
            session["step"] = STATE_CHECK_TIN
            _session_store.set(session_id, session)
            return (
                "CON Enter your phone number\n"
                "or press 0 to use this number:"
            )
        elif user_input == "3":
            _session_store.delete(session_id)
            return self._end_help()
        else:
            # Invalid — show menu again
            return (
                "CON Invalid option.\n"
                "Welcome to DA Revenue\n"
                "1. Register Business\n"
                "2. Check My TIN\n"
                "3. Help"
            )

    def _handle_reg_name(self, session: dict, session_id: str, user_input: str) -> str:
        valid, error = validate_ussd_name(user_input)
        if not valid:
            return f"CON {error}\nEnter your full name:"

        session["collected"]["name"] = user_input.strip()
        session["step"] = STATE_REG_BUSINESS_TYPE
        _session_store.set(session_id, session)
        return (
            "CON Step 2 of 5 - Business Type\n"
            "1. Food Vendor\n"
            "2. Clothing\n"
            "3. Electronics\n"
            "4. Services\n"
            "5. Agriculture\n"
            "6. Other"
        )

    def _handle_reg_business_type(
        self, session: dict, session_id: str, user_input: str
    ) -> str:
        business_type = BUSINESS_TYPE_MAP.get(user_input)
        if not business_type:
            return (
                "CON Invalid option. Choose business type:\n"
                "1. Food Vendor\n"
                "2. Clothing\n"
                "3. Electronics\n"
                "4. Services\n"
                "5. Agriculture\n"
                "6. Other"
            )

        session["collected"]["business_type"] = business_type
        session["step"] = STATE_REG_REGION
        _session_store.set(session_id, session)
        return (
            "CON Step 3 of 5 - Region\n"
            "1. Greater Accra\n"
            "2. Ashanti\n"
            "3. Western\n"
            "4. Northern\n"
            "5. Eastern\n"
            "6. Volta\n"
            "7. Other"
        )

    def _handle_reg_region(self, session: dict, session_id: str, user_input: str) -> str:
        region = REGION_MAP.get(user_input)
        if not region:
            return (
                "CON Invalid option. Choose region:\n"
                "1. Greater Accra\n"
                "2. Ashanti\n"
                "3. Western\n"
                "4. Northern\n"
                "5. Eastern\n"
                "6. Volta\n"
                "7. Other"
            )

        session["collected"]["region"] = region
        session["step"] = STATE_REG_DISTRICT
        _session_store.set(session_id, session)
        return (
            "CON Step 4 of 5\n"
            "Enter market or community name:"
        )

    def _handle_reg_district(self, session: dict, session_id: str, user_input: str) -> str:
        valid, error = validate_ussd_market(user_input)
        if not valid:
            return f"CON {error}\nEnter market or community name:"

        market_name = user_input.strip()
        session["collected"]["market_name"] = market_name
        session["collected"]["district"] = market_name
        session["step"] = STATE_REG_CONFIRM
        _session_store.set(session_id, session)

        c = session["collected"]
        business_label = BUSINESS_TYPE_LABELS.get(c.get("business_type", ""), c.get("business_type", ""))
        return (
            f"CON Step 5 of 5 - Confirm\n"
            f"Name: {c.get('name', '')}\n"
            f"Business: {business_label}\n"
            f"Location: {c.get('region', '')} - {c.get('market_name', '')}\n"
            f"\n"
            f"1. Confirm & Register\n"
            f"2. Start Over"
        )

    def _handle_reg_confirm(
        self,
        session: dict,
        session_id: str,
        msisdn: str,
        user_input: str,
    ) -> str:
        if user_input == "1":
            # Complete registration
            try:
                result = _registration_service.register_trader_ussd(
                    collected=session["collected"],
                    msisdn=normalise_phone(msisdn),
                )
            except TINGenerationError:
                _session_store.delete(session_id)
                return "END Registration failed.\nPlease try again later."
            except Exception as exc:
                logger.exception("USSD registration error: %s", exc)
                _session_store.delete(session_id)
                return "END An error occurred.\nPlease try again later."

            _audit_repo.log({
                "action": "USSD_REG_COMPLETE",
                "entity_type": "trader",
                "entity_id": result.get("trader_id"),
                "actor_type": "trader",
                "channel": "ussd",
                "details": {
                    "tin_number": result.get("tin_number"),
                    "msisdn": msisdn,
                },
            })
            _session_store.delete(session_id)
            return (
                f"END Registration complete!\n"
                f"Your TIN: {result['tin_number']}\n"
                f"An SMS will be sent shortly."
            )

        elif user_input == "2":
            # Start over
            session["step"] = STATE_MAIN_MENU
            session["collected"] = {}
            _session_store.set(session_id, session)
            return _main_menu_text()
        else:
            # Re-show confirm screen
            c = session["collected"]
            business_label = BUSINESS_TYPE_LABELS.get(c.get("business_type", ""), c.get("business_type", ""))
            return (
                f"CON Invalid option.\n"
                f"Name: {c.get('name', '')}\n"
                f"Business: {business_label}\n"
                f"Location: {c.get('region', '')} - {c.get('market_name', '')}\n"
                f"\n"
                f"1. Confirm & Register\n"
                f"2. Start Over"
            )

    def _handle_check_tin(
        self,
        session: dict,
        session_id: str,
        msisdn: str,
        user_input: str,
    ) -> str:
        if user_input == "0":
            phone = normalise_phone(msisdn)
        else:
            valid, error = validate_ussd_phone(user_input)
            if not valid:
                return (
                    f"CON {error}\n"
                    "Enter phone number or 0 for this number:"
                )
            phone = normalise_phone(user_input)

        _session_store.delete(session_id)
        result = _tin_service.lookup_tin(phone)

        if result:
            return f"END Your TIN is {result['tin_number']}"
        else:
            return "END No registration found for that number."

    @staticmethod
    def _end_help() -> str:
        return (
            "END For help registering:\n"
            "Dial *XXX# and follow steps.\n"
            "Visit your District Assembly office.\n"
            "Or register online at the DA website."
        )

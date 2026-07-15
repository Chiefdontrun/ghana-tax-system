"""
USSD webhook view — POST /ussd/callback

Supports:
  - Arkesel JSON payloads (live shortcode *928*309#)
  - Africa's Talking form-encoded payloads (legacy tests)

Arkesel live behaviour (captured 2026-07-15, session 17841474871496131):
  Request 1: newSession=true,  userData="*928*309#"  (dialed shortcode — NOT empty)
  Request 2: newSession=false, userData="1"          (single step input only)

So newSession is the only reliable first-dial signal, and userData never
accumulates with * separators (Possibility A). Session step state lives in
USSDSessionStore keyed by sessionID.
"""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

from apps.audit.repository import AuditRepository
from apps.ussd.state_machine import USSDStateMachine

logger = logging.getLogger(__name__)

_state_machine = USSDStateMachine()
_audit_repo = AuditRepository()


def _is_arkesel_payload(data) -> bool:
    """True when the request looks like Arkesel's JSON webhook shape."""
    if not hasattr(data, "get"):
        return False
    return "userData" in data or "sessionID" in data


def adapt_gateway_input(data) -> dict:
    """
    Normalise gateway-specific fields into state-machine arguments.

    Returns dict with keys: session_id, msisdn, text, input_mode, user_id, network, is_arkesel
      input_mode: "arkesel" | "africas_talking"
    """
    is_arkesel = _is_arkesel_payload(data)
    session_id = data.get("sessionID") or data.get("sessionId") or ""
    msisdn = data.get("msisdn") or data.get("phoneNumber") or ""
    user_id = data.get("userID") or data.get("userId") or ""
    network = data.get("network") or ""

    if is_arkesel:
        # Possibility A: userData is only the current step's keypress (or the
        # dialed shortcode on newSession). Never treat it as AT-style history.
        new_session = bool(data.get("newSession", False))
        raw = data.get("userData")
        raw = "" if raw is None else str(raw)
        text = "" if new_session else raw.strip()
        return {
            "session_id": session_id,
            "msisdn": msisdn,
            "text": text,
            "input_mode": "arkesel",
            "user_id": user_id,
            "network": network,
            "is_arkesel": True,
            "new_session": new_session,
        }

    return {
        "session_id": session_id,
        "msisdn": msisdn,
        "text": data.get("text", "") or "",
        "input_mode": "africas_talking",
        "user_id": user_id,
        "network": network,
        "is_arkesel": False,
        "new_session": None,
    }


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(ratelimit(key="ip", rate="100/m", method="POST", block=True), name="dispatch")
class USSDCallbackView(View):
    def post(self, request) -> HttpResponse:
        try:
            data = json.loads(request.body)
        except ValueError:
            # Africa's Talking form-encoded payloads (legacy tests)
            data = request.POST

        adapted = adapt_gateway_input(data)
        session_id = adapted["session_id"]
        msisdn = adapted["msisdn"]
        text = adapted["text"]
        user_id = adapted["user_id"]
        input_mode = adapted["input_mode"]

        logger.info(
            "USSD callback | gateway=%s session=%s phone=%s newSession=%s text_len=%d",
            input_mode,
            session_id,
            msisdn,
            adapted.get("new_session"),
            len(text),
        )

        if not session_id or not msisdn:
            logger.warning("USSD callback missing sessionId or phoneNumber")
            return HttpResponse(
                "END Invalid request.",
                content_type="text/plain",
                status=400,
            )

        try:
            response_text = _state_machine.process(
                session_id=session_id,
                msisdn=msisdn,
                text=text,
                input_mode=input_mode,
            )
        except Exception as exc:
            logger.exception("Unhandled USSD error for session %s: %s", session_id, exc)
            response_text = "END An error occurred. Please try again."

        if adapted["is_arkesel"]:
            continue_session = response_text.startswith("CON")
            message = response_text[4:] if len(response_text) > 4 else response_text
            return JsonResponse(
                {
                    "sessionID": session_id,
                    "userID": user_id,
                    "msisdn": msisdn,
                    "message": message,
                    "continueSession": continue_session,
                }
            )

        return HttpResponse(response_text, content_type="text/plain")


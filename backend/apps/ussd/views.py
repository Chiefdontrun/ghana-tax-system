"""
USSD webhook view — POST /ussd/callback
Receives Arkesel JSON USSD webhook payload and routes through
the USSDStateMachine. Returns JSON responses.
"""

import logging
import json

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from apps.audit.repository import AuditRepository
from apps.ussd.state_machine import USSDStateMachine

logger = logging.getLogger(__name__)

_state_machine = USSDStateMachine()
_audit_repo = AuditRepository()


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(ratelimit(key="ip", rate="100/m", method="POST", block=True), name="dispatch")
class USSDCallbackView(View):
    def post(self, request) -> HttpResponse:
        try:
            data = json.loads(request.body)
        except ValueError:
            # Fallback for Africa's Talking form-encoded payloads so old tests pass if needed
            # (Though Arkesel will strictly send JSON)
            data = request.POST

        session_id = data.get("sessionID") or data.get("sessionId", "")
        msisdn = data.get("msisdn") or data.get("phoneNumber", "")
        # Arkesel uses userData. Africa's Talking uses text.
        text = data.get("userData", "") if "userData" in data else data.get("text", "")
        user_id = data.get("userID", "")
        
        # In Arkesel, if newSession=True, the user just dialed the shortcode.
        # But state_machine.py relies on the session store to know if it's new.
        
        logger.info(
            "USSD callback | session=%s phone=%s text_len=%d",
            session_id, msisdn, len(text),
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
            )
        except Exception as exc:
            logger.exception("Unhandled USSD error for session %s: %s", session_id, exc)
            response_text = "END An error occurred. Please try again."

        # Support both Arkesel JSON and AT plain-text responses
        if "userData" in data:
            # Arkesel JSON response
            continue_session = response_text.startswith("CON")
            message = response_text[4:] if len(response_text) > 4 else response_text
            return JsonResponse({
                "sessionID": session_id,
                "userID": user_id,
                "msisdn": msisdn,
                "message": message,
                "continueSession": continue_session
            })
        else:
            # AT plain-text response (legacy support for old tests)
            return HttpResponse(response_text, content_type="text/plain")


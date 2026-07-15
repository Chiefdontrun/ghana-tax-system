"""
Temporary raw-logging endpoint for Arkesel USSD payload capture.

POST /ussd/arkesel-capture/

Appends every request (body + headers) to arkesel_payloads_capture.jsonl
and mirrors the latest request to arkesel_payload.json for convenience.

Returns a minimal Arkesel-compatible JSON response so a live multi-step
session can continue far enough to capture a follow-up userData payload.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# Written under backend/ (cwd when runserver starts from backend/)
_CAPTURE_JSONL = Path("arkesel_payloads_capture.jsonl")
_CAPTURE_LATEST = Path("arkesel_payload.json")


def _capture_paths() -> tuple[Path, Path]:
    """Prefer BASE_DIR so paths are stable even if cwd differs."""
    base = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    return base / "arkesel_payloads_capture.jsonl", base / "arkesel_payload.json"


@method_decorator(csrf_exempt, name="dispatch")
class ArkeselCaptureView(View):
    """Log raw Arkesel webhooks; return harmless CON/continue responses."""

    def dispatch(self, request, *args, **kwargs):
        body_raw = request.body.decode("utf-8", errors="replace")
        try:
            body_json = json.loads(body_raw) if body_raw.strip() else {}
        except ValueError:
            body_json = {}

        record = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "headers": dict(request.headers),
            "GET": dict(request.GET),
            "POST": dict(request.POST),
            "body_raw": body_raw,
            "body_json": body_json if isinstance(body_json, dict) else {},
        }

        jsonl_path, latest_path = _capture_paths()
        try:
            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            logger.info(
                "Arkesel capture | session=%s newSession=%s userData=%r → %s",
                body_json.get("sessionID") or body_json.get("sessionId"),
                body_json.get("newSession"),
                body_json.get("userData") or body_json.get("text"),
                jsonl_path,
            )
        except OSError as exc:
            logger.exception("Failed to write Arkesel capture: %s", exc)

        # Arkesel JSON shape (when payload looks like Arkesel)
        if isinstance(body_json, dict) and (
            "userData" in body_json or "sessionID" in body_json or "sessionId" in body_json
        ):
            session_id = body_json.get("sessionID") or body_json.get("sessionId") or ""
            user_id = body_json.get("userID") or body_json.get("userId") or ""
            msisdn = body_json.get("msisdn") or body_json.get("phoneNumber") or ""
            new_session = body_json.get("newSession")
            if new_session is None:
                # Fallback heuristic only for capture UX — not production parsing
                ud = str(body_json.get("userData") or "")
                new_session = ud.startswith("*") and ud.endswith("#")

            if new_session:
                message = (
                    "CAPTURE OK (step 1)\n"
                    "Select any option so we can capture request #2:\n"
                    "1. Continue\n"
                    "2. Exit"
                )
            else:
                message = (
                    "CAPTURE OK (follow-up)\n"
                    f"Received userData={body_json.get('userData')!r}\n"
                    "You can end the session now."
                )

            return JsonResponse(
                {
                    "sessionID": session_id,
                    "userID": user_id,
                    "msisdn": msisdn,
                    "message": message,
                    "continueSession": bool(new_session),
                }
            )

        # Plain-text fallback for non-JSON probes
        return HttpResponse(
            "CON CAPTURE OK - select 1 to continue",
            status=200,
            content_type="text/plain",
        )

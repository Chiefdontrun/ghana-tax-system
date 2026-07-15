"""
Arkesel USSD capture / safety endpoint — POST /ussd/arkesel-capture/

Production shortcode must point at POST /ussd/callback/. If the Arkesel
dashboard is still pointed here (or gets pointed here by mistake), this
view MUST still run the real state machine so traders are not locked out.

Behaviour:
  1. Best-effort raw payload log (local disk or /tmp on serverless).
  2. CRITICAL log that production traffic hit the capture path.
  3. Hand off to USSDCallbackView — same response as /ussd/callback/.

On Vercel the filesystem under /var/task is read-only; file logging uses
tempfile.gettempdir() and never fails the request.
"""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def _capture_paths() -> tuple[Path, Path]:
    """
    Writable paths for capture files.
    Prefer BASE_DIR when writable (local runserver); else system temp
    (Vercel / serverless read-only /var/task).
    """
    candidates = [
        Path(getattr(settings, "BASE_DIR", Path.cwd())),
        Path(tempfile.gettempdir()),
    ]
    for base in candidates:
        try:
            base.mkdir(parents=True, exist_ok=True)
            probe = base / ".ussd_capture_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return base / "arkesel_payloads_capture.jsonl", base / "arkesel_payload.json"
        except OSError:
            continue
    # Last resort — still under temp; write may fail and is swallowed
    tmp = Path(tempfile.gettempdir())
    return tmp / "arkesel_payloads_capture.jsonl", tmp / "arkesel_payload.json"


def _best_effort_log(request, body_raw: str, body_json: dict) -> None:
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
            "Arkesel capture log | session=%s newSession=%s userData=%r → %s",
            body_json.get("sessionID") or body_json.get("sessionId"),
            body_json.get("newSession"),
            body_json.get("userData") or body_json.get("text"),
            jsonl_path,
        )
    except OSError as exc:
        # Never fail the USSD session over logging (read-only /var/task, etc.)
        logger.warning(
            "Arkesel capture file log skipped (%s). Payload still processed. "
            "session=%s userData=%r",
            exc,
            body_json.get("sessionID") or body_json.get("sessionId"),
            body_json.get("userData") or body_json.get("text"),
        )


@method_decorator(csrf_exempt, name="dispatch")
class ArkeselCaptureView(View):
    """
    Safety net: log + run the real USSD callback.

    Do not leave Arkesel pointed here long-term — repoint to /ussd/callback/ —
    but while misconfigured, traders still get the state machine.
    """

    def dispatch(self, request, *args, **kwargs):
        body_raw = request.body.decode("utf-8", errors="replace")
        try:
            body_json = json.loads(body_raw) if body_raw.strip() else {}
        except ValueError:
            body_json = {}

        if not isinstance(body_json, dict):
            body_json = {}

        _best_effort_log(request, body_raw, body_json)

        logger.critical(
            "LIVE traffic hit /ussd/arkesel-capture/ — processing via state machine "
            "anyway. Repoint Arkesel to "
            "https://ghana-tax-system-hh6f.vercel.app/ussd/callback/"
        )

        # Delegate to the real callback so sessions work even if dashboard is wrong.
        # Import inside method to avoid circular imports at module load.
        from apps.ussd.views import USSDCallbackView

        return USSDCallbackView.as_view()(request, *args, **kwargs)

import time
import json
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# File to persist live state – shared between doctor & patient, survives reloads
STATE_FILE = Path(settings.BASE_DIR) / "media" / "live_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_STATE = {
    "live": False,
    "since": None,
    "by": None,  # "doctor" | "patient" | None
}

def _read_state():
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return dict(DEFAULT_STATE)

def _write_state(state):
    try:
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass

@csrf_exempt
def live_status(request):
    """GET -> {live, since, by}. Used by polling on both sides."""
    state = _read_state()
    return JsonResponse(state)

@csrf_exempt
def live_toggle(request):
    """
    POST -> toggle or set live state.
    Body: {"live": true/false}  (optional, if missing toggles)
    Also accepts form-encoded live=1/0
    Returns new state.
    """
    state = _read_state()

    # determine desired value
    desired = None
    try:
        if request.content_type and "application/json" in request.content_type:
            body = json.loads(request.body.decode() or "{}")
            if "live" in body:
                desired = bool(body["live"])
        if desired is None:
            v = request.POST.get("live")
            if v is not None:
                desired = v in ("1", "true", "True", "on")
        if desired is None and request.body:
            # also try json without content-type
            try:
                body = json.loads(request.body.decode() or "{}")
                if "live" in body:
                    desired = bool(body["live"])
            except Exception:
                pass
    except Exception:
        pass

    if desired is None:
        desired = not state.get("live", False)

    # detect role from referrer/path or session
    by = None
    ref = request.META.get("HTTP_REFERER", "")
    if "/doctor" in ref or "/doctor" in request.path:
        by = "doctor"
    elif "/patient" in ref or "/patient" in request.path:
        by = "patient"
    # also allow explicit 'by' in body
    try:
        body = json.loads(request.body.decode() or "{}")
        if body.get("by") in ("doctor", "patient"):
            by = body["by"]
    except Exception:
        pass
    if not by:
        # fallback to query param
        by = request.GET.get("by")
        if by not in ("doctor", "patient"):
            # guess from current live state holder
            by = state.get("by") or "patient"

    if desired:
        state = {"live": True, "since": int(time.time()), "by": by}
    else:
        state = {"live": False, "since": None, "by": None}

    _write_state(state)
    return JsonResponse(state)

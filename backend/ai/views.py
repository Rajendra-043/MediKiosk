from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import ask_ai, build_suggestions_and_otc


@csrf_exempt
def ai_assist(request):
    """
    LIVE button background assistant.
    Takes a user problem / navigation request and returns:
    - answer (from main AI)
    - action {type, url, label} for navigation when intent is clear
    - quick_links for patient-side pages
    - chatbot_url to continue in full chatbot with handoff
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed"},
            status=405
        )

    text = request.POST.get("question") or request.POST.get("text")
    role = request.POST.get("role") or ""

    if not text and request.body:
        try:
            import json as _json
            data = _json.loads(request.body.decode() or "{}")
            text = data.get("question") or data.get("text")
            role = data.get("role") or role
        except Exception:
            pass

    if not text:
        return JsonResponse({"error": "Question is required"}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key or "_default"

    # Detect role from referer if not supplied
    if role not in ("doctor", "patient"):
        ref = request.META.get("HTTP_REFERER", "")
        if "/doctor" in ref:
            role = "doctor"
        else:
            role = "patient"

    low = text.lower()

    def _has(*words):
        return any(w in low for w in words)

    action = None
    if role == "doctor":
        if _has("dashboard", "home", "patient list"):
            action = {"type": "navigate", "url": "/doctor/dashboard/", "label": "Go to Doctor Dashboard"}
        elif _has("profile"):
            action = {"type": "navigate", "url": "/doctor/profile/", "label": "Go to Doctor Profile"}
        elif _has("patient", "detail", "record"):
            action = {"type": "navigate", "url": "/doctor/dashboard/", "label": "Go to Patients"}
        elif _has("chat", "chatbot", "assistant", "talk", "problem", "help"):
            action = {"type": "chatbot", "url": "/patient/chatbot/", "label": "Open AI Chatbot"}
    else:
        if _has("dashboard", "home"):
            action = {"type": "navigate", "url": "/patient/dashboard/", "label": "Go to Dashboard"}
        elif _has("document", "report", "upload", "pdf", "prescription scan"):
            action = {"type": "navigate", "url": "/patient/documents/", "label": "Go to Documents"}
        elif _has("medicine", "medication", "tablet", "dose", "prescription"):
            action = {"type": "navigate", "url": "/patient/medications/", "label": "Go to Medications"}
        elif _has("history"):
            action = {"type": "navigate", "url": "/patient/medical-history/", "label": "Go to Medical History"}
        elif _has("timeline"):
            action = {"type": "navigate", "url": "/patient/timeline/", "label": "Go to Timeline"}
        elif _has("profile", "account", "my info"):
            action = {"type": "navigate", "url": "/patient/profile/", "label": "Go to Profile"}
        elif _has("chat", "chatbot", "assistant", "talk", "problem", "symptom", "pain", "fever", "help", "doctor"):
            action = {"type": "chatbot", "url": "/patient/chatbot/", "label": "Open AI Chatbot"}

    # Always get a background AI answer too so LIVE feels like an assistant
    try:
        answer = ask_ai(text, session_id=session_id)
    except Exception:
        if action:
            answer = f"I can help with that. {action['label']} or continue chatting below."
        else:
            answer = "I'm your Live assistant. Tell me your problem and I'll guide you or open the chatbot for you."

    if role == "doctor":
        quick_links = [
            {"label": "Dashboard", "url": "/doctor/dashboard/"},
            {"label": "Profile", "url": "/doctor/profile/"},
            {"label": "Patients", "url": "/doctor/dashboard/"},
        ]
        chatbot_url = "/patient/chatbot/"
    else:
        quick_links = [
            {"label": "Dashboard", "url": "/patient/dashboard/"},
            {"label": "Chatbot", "url": "/patient/chatbot/"},
            {"label": "Documents", "url": "/patient/documents/"},
            {"label": "Medications", "url": "/patient/medications/"},
            {"label": "History", "url": "/patient/medical-history/"},
            {"label": "Timeline", "url": "/patient/timeline/"},
        ]
        chatbot_url = "/patient/chatbot/"

    suggestions, otc_info = build_suggestions_and_otc(session_id=session_id)

    return JsonResponse({
        "question": text,
        "answer": answer,
        "action": action,
        "quick_links": quick_links,
        "chatbot_url": chatbot_url,
        "suggestions": suggestions,
        "otc_info": otc_info,
    })


@csrf_exempt
def ai_chat(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed"},
            status=405
        )

    question = request.POST.get("question") or request.POST.get("text")

    if not question and request.body:
        try:
            import json as _json
            data = _json.loads(request.body.decode() or "{}")
            question = data.get("question") or data.get("text")
        except Exception:
            pass

    if not question:
        return JsonResponse(
            {"error": "Question is required"},
            status=400
        )

    # Use session key as session_id for per-user state.
    # NOTE: session.create() returns None, so capture the key afterwards.
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key or "_default"

    answer = ask_ai(question, session_id=session_id)

    # Also provide structured suggestions + general OTC info whenever available
    # so the frontend can show a dedicated suggestions card.
    suggestions, otc_info = build_suggestions_and_otc(session_id=session_id)

    return JsonResponse({
        "question": question,
        "answer": answer,
        "suggestions": suggestions,
        "otc_info": otc_info,
        "disclaimer": "General information only — not medical advice. Follow package label and consult a pharmacist or doctor. Seek prompt care for severe or chest pain."
    })
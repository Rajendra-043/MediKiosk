from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ai.services import ask_ai, build_suggestions_and_otc


@csrf_exempt
def voice_chat(request):
    """
    Non-blocking voice endpoint: accepts text (from browser STT)
    and returns AI answer + TTS hint. The blocking mic loop
    listen_and_ask() is for CLI use only.
    """
    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST requests are allowed."
        }, status=405)

    # Accept JSON or form-encoded question/text
    question = None
    try:
        import json as _json
        if request.content_type and "application/json" in request.content_type:
            body = _json.loads(request.body.decode() or "{}")
            question = body.get("question") or body.get("text")
    except Exception:
        pass

    if not question:
        question = request.POST.get("question") or request.POST.get("text")

    if not question:
        return JsonResponse({
            "error": "question/text is required"
        }, status=400)

    # Use session key as session_id for per-user state.
    # NOTE: session.create() returns None, so capture the key afterwards.
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key or "_default"

    # optional: handle exit commands without calling LLM
    cmd = question.lower().strip()
    if cmd in {"exit", "quit", "stop", "goodbye", "end session"}:
        return JsonResponse({
            "question": question,
            "answer": "Thank you. Your session has ended. Goodbye.",
            "finished": True
        })

    answer = ask_ai(question, session_id=session_id)

    suggestions, otc_info = build_suggestions_and_otc(session_id=session_id)

    return JsonResponse({
        "question": question,
        "answer": answer,
        "suggestions": suggestions,
        "otc_info": otc_info,
        "disclaimer": "General information only — not medical advice. Follow package label and consult a pharmacist or doctor."
    })
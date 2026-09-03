from django.http import JsonResponse
from .services import listen_and_ask


def voice_chat(request):
    if request.method == "POST":
        question, answer = listen_and_ask()

        return JsonResponse({
            "question": question,
            "answer": answer
        })

    return JsonResponse({
        "error": "Only POST requests are allowed."
    }, status=405)
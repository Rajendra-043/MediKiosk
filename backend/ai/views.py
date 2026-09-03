from django.http import JsonResponse
from .services import ask_ai


def ai_chat(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed"},
            status=405
        )

    question = request.POST.get("question")

    if not question:
        return JsonResponse(
            {"error": "Question is required"},
            status=400
        )

    answer = ask_ai(question)

    return JsonResponse({
        "question": question,
        "answer": answer
    })
# Create your views here.

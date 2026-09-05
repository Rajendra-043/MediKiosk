from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import ask_ai


@csrf_exempt
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
from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/ask-ai/<int:patient_id>/",
        views.ask_ai_about_patient_api,
        name="ask_ai_about_patient_api"
    ),
]
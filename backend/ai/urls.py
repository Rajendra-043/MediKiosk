from django.urls import path
from . import views


urlpatterns = [

    path(
        "chat/",
        views.ai_chat,
        name="ai_chat"
    ),

    path(
        "assist/",
        views.ai_assist,
        name="ai_assist"
    ),

]
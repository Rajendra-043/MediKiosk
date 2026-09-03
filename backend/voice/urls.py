from django.urls import path ,include
from .views import voice_chat


urlpatterns = [
    path("chat/", voice_chat, name="voice_chat"),

    path("voice/", include("voice.urls")),
]
from django.urls import path
from .views import voice_chat


urlpatterns = [
    path("chat/", voice_chat, name="voice_chat"),
]
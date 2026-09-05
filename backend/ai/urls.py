from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [

    path("admin/", admin.site.urls),

    path("api/ai/", include("ai.urls")),

    path("chat/", views.ai_chat, name="ai_chat"),

]

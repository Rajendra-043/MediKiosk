from django.urls import path
from .views import live_status, live_toggle

urlpatterns = [
    path("status/", live_status, name="live_status"),
    path("toggle/", live_toggle, name="live_toggle"),
]

from django.urls import path

from . import views

urlpatterns = [
    path("", views.abha_home, name="abha_home"),
    path("link/", views.abha_link, name="abha_link"),
    path("create/", views.abha_create, name="abha_create"),
    path("card/", views.abha_card, name="abha_card"),
    path("unlink/", views.abha_unlink, name="abha_unlink"),
]

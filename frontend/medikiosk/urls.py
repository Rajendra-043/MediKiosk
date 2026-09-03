from django.contrib import admin
from django.urls import path
from django.shortcuts import render


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    # Landing
    path(
        "",
        lambda request:
        render(request, "landing/index.html")
    ),

    # Patient
    path(
        "patient/",
        lambda request:
        render(request, "patient/landing.html")
    ),

    path(
        "patient/login/",
        lambda request:
        render(request, "patient/login.html")
    ),

    path(
        "patient/register/",
        lambda request:
        render(request, "patient/register.html")
    ),

    path(
        "patient/dashboard/",
        lambda request:
        render(request, "patient/dashboard.html")
    ),

    # Doctor
    path(
        "doctor/",
        lambda request:
        render(request, "doctor/landing.html")
    ),

    path(
        "doctor/login/",
        lambda request:
        render(request, "doctor/login.html")
    ),

    path(
        "doctor/register/",
        lambda request:
        render(request, "doctor/register.html")
    ),
]
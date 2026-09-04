"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views


urlpatterns = [

    # -------------------------
    # HOME
    # -------------------------

    path(
        "",
        views.home,
        name="home"
    ),


    # -------------------------
    # PATIENT
    # -------------------------

    path(
        "patient/",
        views.patient_landing,
        name="patient_landing"
    ),

    path(
        "patient/login/",
        views.patient_login,
        name="patient_login"
    ),

    path(
        "patient/register/",
        views.patient_register,
        name="patient_register"
    ),

    path(
        "patient/dashboard/",
        views.patient_dashboard,
        name="patient_dashboard"
    ),


    # -------------------------
    # DOCTOR
    # -------------------------

    path(
        "doctor/",
        views.doctor_landing,
        name="doctor_landing"
    ),

    path(
        "doctor/login/",
        views.doctor_login,
        name="doctor_login"
    ),

    path(
        "doctor/register/",
        views.doctor_register,
        name="doctor_register"
    ),


    # -------------------------
    # ADMIN
    # -------------------------

    path(
        "admin/",
        admin.site.urls
    ),
]
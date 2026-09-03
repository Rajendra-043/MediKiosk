from django.shortcuts import render


def home(request):
    return render(request, "landing/index.html")


# -------------------------
# PATIENT
# -------------------------

def patient_landing(request):
    return render(request, "paitent/landing.html")


def patient_login(request):
    return render(request, "paitent/login.html")


def patient_register(request):
    return render(request, "paitent/register.html")


def patient_dashboard(request):
    return render(request, "paitent/dashboard.html")


# -------------------------
# DOCTOR
# -------------------------

def doctor_landing(request):
    return render(request, "doctor/landing.html")


def doctor_login(request):
    return render(request, "doctor/login.html")


def doctor_register(request):
    return render(request, "doctor/register.html")
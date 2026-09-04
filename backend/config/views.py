from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password

from patients.models import Patient
from doctor.models import Doctor


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

    if request.method == "POST":

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request,
                "paitent/register.html",
                {"error": "Passwords do not match."}
            )

        patient = Patient.objects.create(
            name=request.POST.get("name"),
            date_of_birth=request.POST.get("date_of_birth"),
            gender=request.POST.get("gender"),
            blood_group=request.POST.get("blood_group", ""),
            phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""),
            address=request.POST.get("address", ""),
            passward=make_password(password),
        )

        # Automatically create Patient ID
        patient.patient_id = f"PAT{patient.id:04d}"
        patient.save()

        return redirect("/patient/login/")

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

    if request.method == "POST":

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request,
                "doctor/register.html",
                {"error": "Passwords do not match."}
            )

        doctor = Doctor.objects.create(
            full_name=request.POST.get("full_name"),
            medical_registration_number=request.POST.get(
                "medical_registration_number"
            ),
            specialization=request.POST.get("specialization"),
            qualification=request.POST.get("qualification"),
            experience=request.POST.get("experience") or 0,
            phone=request.POST.get("phone"),
            email=request.POST.get("email"),
        )

        # Automatically create Doctor ID
        doctor.doctor_id = f"DOC{doctor.id:04d}"
        doctor.save()

        return redirect("/doctor/login/")

    return render(request, "doctor/register.html")
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password

from patients.models import Patient, MedicalHistory, Medication, MedicalDocument
from doctor.models import Doctor


def home(request):
    return render(request, "landing/index.html")


# -------------------------
# PATIENT
# -------------------------

def patient_landing(request):
    return render(request, "paitent/landing.html")


def patient_login(request):
    if request.method == "POST":
        identifier = request.POST.get("patient_id")
        password = request.POST.get("password")

        # Patient ID ya Email se match karo
        try:
            if "@" in identifier:
                patient = Patient.objects.get(email=identifier)
            else:
                patient = Patient.objects.get(patient_id=identifier)
        except Patient.DoesNotExist:
            return render(request, "paitent/login.html", {"error": "Invalid Patient ID / Email or Password."})

        # Hashed password match karo
        if check_password(password, patient.passward):
            request.session["patient_id"] = patient.id
            return redirect("/patient/dashboard/")
        else:
            return render(request, "paitent/login.html", {"error": "Invalid Patient ID / Email or Password."})

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
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("/patient/login/")
    
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, "paitent/dashboard.html", {"patient": patient})


def patient_logout(request):
    request.session.flush()
    return redirect("/patient/login/")


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

        doctor.doctor_id = f"DOC{doctor.id:04d}"
        doctor.save()

        return redirect("/doctor/login/")

    return render(request, "doctor/register.html")


# -------------------------
# MEDICAL HISTORY
# -------------------------

def medical_history(request):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("/patient/login/")

    patient = get_object_or_404(Patient, id=patient_id)

    medical_history = MedicalHistory.objects.filter(
        patient=patient
    ).order_by("-diagnosed_date", "-created_at")

    records = []
    for record in medical_history:
        records.append({
            "title": record.condition,
            "category": "condition",
            "date": record.diagnosed_date,
            "description": record.diagnosis,
            "doctor": record.doctor_name,
            "hospital": "",
            "status": "",
        })

    return render(
        request,
        "paitent/medical_history.html",
        {
            "patient": patient,
            "medical_history": records,
        }
    )


# -------------------------
# MEDICATIONS
# -------------------------

def medications(request):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("/patient/login/")

    patient = get_object_or_404(Patient, id=patient_id)

    medication_records = Medication.objects.filter(
        patient=patient
    ).order_by("-created_at")

    return render(
        request,
        "paitent/medication.html",
        {
            "patient": patient,
            "medications": medication_records,
        }
    )


# -------------------------
# DOCUMENTS
# -------------------------

def documents(request):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("/patient/login/")

    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        document_name = request.POST.get("document_name", "")

        if uploaded_file:
            MedicalDocument.objects.create(
                patient=patient,
                document_name=document_name or uploaded_file.name,
                file=uploaded_file,
                document_type=uploaded_file.content_type,
            )
        return redirect("/patient/documents/")

    document_records = MedicalDocument.objects.filter(
        patient=patient
    ).order_by("-uploaded_at")

    return render(
        request,
        "paitent/documents.html",
        {
            "patient": patient,
            "documents": document_records,
        }
    )


def delete_document(request, doc_id):
    if request.method == "POST":
        document = get_object_or_404(MedicalDocument, id=doc_id)
        if document.file:
            document.file.delete(save=False)
        document.delete()
    return redirect('documents')
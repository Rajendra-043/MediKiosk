from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password

from patients.models import Patient, MedicalHistory, Medication, MedicalDocument
from doctor.models import Doctor
from django.views.decorators.http import require_POST


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


def patient_chatbot(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("/patient/login/")

    patient = get_object_or_404(Patient, id=patient_id)

    return render(
        request,
        "paitent/ai-chatbot.html",
        {
            "patient": patient,
        }
    )


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

# PROFILE
def profile(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("/patient/login/")

    patient = get_object_or_404(Patient, id=patient_id)

    return render(request, "paitent/profile.html", {
        "patient": patient,
    })



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

    document_records = MedicalDocument.objects.filter(
        patient=patient
    ).order_by("-uploaded_at")

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        document_name = request.POST.get("document_name", "").strip()

        if not uploaded_file:
            return render(
                request,
                "paitent/documents.html",
                {
                    "patient": patient,
                    "documents": document_records,
                    "error": "Please select a document."
                }
            )

        # Allowed file types
        allowed_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".jpg",
            ".jpeg",
            ".png",
        }

        file_extension = Path(uploaded_file.name).suffix.lower()

        if file_extension not in allowed_extensions:
            return render(
                request,
                "paitent/documents.html",
                {
                    "patient": patient,
                    "documents": document_records,
                    "error": "Only PDF, DOC, DOCX, JPG, JPEG and PNG files are allowed."
                }
            )

        # Maximum file size = 5 MB
        max_file_size = 5 * 1024 * 1024

        if uploaded_file.size > max_file_size:
            return render(
                request,
                "paitent/documents.html",
                {
                    "patient": patient,
                    "documents": document_records,
                    "error": "File size must be 5 MB or less."
                }
            )

        # Save document
        MedicalDocument.objects.create(
            patient=patient,
            document_name=document_name or uploaded_file.name,
            file=uploaded_file,
            document_type=uploaded_file.content_type,
        )

        return redirect("/patient/documents/")

    return render(
        request,
        "paitent/documents.html",
        {
            "patient": patient,
            "documents": document_records,
        }
    )

# -------------------------
# DELETE DOCUMENT
# -------------------------

@require_POST
def delete_document(request, doc_id):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("/patient/login/")

    document = get_object_or_404(
        MedicalDocument,
        id=doc_id,
        patient_id=patient_id
    )

    if document.file:
        document.file.delete(save=False)

    document.delete()

    return redirect("/patient/documents/")

# ------------------------
# HISTORY TIMELINE
# ------------------------

def timeline(request):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return redirect("/patient/login/")
        
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Testing ke liye sample dummy data
    timeline_events = [
        
    ]
    
    return render(request, "paitent/History_Timline.html", {
        "patient": patient,
        "timeline": timeline_events,
    })


def document_detail(request, doc_id):

    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("/patient/login/")

    patient = get_object_or_404(
        Patient,
        id=patient_id
    )

    document = get_object_or_404(
        MedicalDocument,
        id=doc_id,
        patient=patient
    )

    return render(
        request,
        "paitent/document_detail.html",
        {
            "patient": patient,
            "document": document,
        }
    )

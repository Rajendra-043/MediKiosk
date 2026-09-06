from django.http import JsonResponse
from django.views.decorators.http import require_POST

from patients.models import Patient, MedicalDocument
from .ocr_engine import extract_text


@require_POST
def process_document(request):

    # -------------------------
    # Get logged-in patient
    # -------------------------

    patient_id = request.session.get("patient_id")

    if not patient_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Patient is not logged in."
            },
            status=401
        )

    patient = Patient.objects.filter(
        id=patient_id
    ).first()

    if not patient:
        return JsonResponse(
            {
                "success": False,
                "error": "Patient not found."
            },
            status=404
        )

    # -------------------------
    # Get uploaded file
    # -------------------------

    uploaded_file = request.FILES.get("document")

    if not uploaded_file:
        return JsonResponse(
            {
                "success": False,
                "error": "No document uploaded."
            },
            status=400
        )

    try:

        # -------------------------
        # STEP 1
        # Save document first
        # -------------------------

        document = MedicalDocument.objects.create(
            patient=patient,
            document_name=uploaded_file.name,
            document_type=uploaded_file.content_type,
            file=uploaded_file
        )

        # -------------------------
        # STEP 2
        # Run OCR
        # -------------------------

        text = extract_text(
            document.file.path
        )

        # -------------------------
        # STEP 3
        # Generate report
        # -------------------------

        report = f"""Medical Document Report

Patient Information:
Patient Name: {patient.name}

Extracted Information:
{text}

OCR Status:
Text successfully extracted from the uploaded document.
"""

        # -------------------------
        # STEP 4
        # Store OCR data
        # -------------------------

        document.extracted_text = text
        document.report = report

        document.save(
            update_fields=[
                "extracted_text",
                "report"
            ]
        )

        # -------------------------
        # STEP 5
        # Return response
        # -------------------------

        return JsonResponse(
            {
                "success": True,
                "filename": document.document_name,
                "text": document.extracted_text,
                "report": document.report,
                "document_id": document.id
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=500
        )
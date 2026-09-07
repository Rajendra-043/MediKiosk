from django.http import JsonResponse
from django.views.decorators.http import require_POST

from patients.models import Patient, Medication, MedicalDocument

from .ocr_engine import extract_text
from .data_extractor import extract_medical_data


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
    # Get uploaded document
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
        # Save uploaded document
        # -------------------------

        document = MedicalDocument.objects.create(
            patient=patient,
            document_name=uploaded_file.name,
            file=uploaded_file,
            document_type=uploaded_file.content_type
        )

        # -------------------------
        # Run OCR
        # -------------------------

        text = extract_text(
            document.file.path
        )

        # -------------------------
        # Store raw OCR text
        # -------------------------

        document.extracted_text = text

        # -------------------------
        # Extract structured data
        # -------------------------

        medical_data = extract_medical_data(text)

        # -------------------------
        # Store detected document type
        # -------------------------

        document.document_type = medical_data["document_type"]

        # -------------------------
        # Save medication
        # -------------------------

        if medical_data["medicine"]:

            Medication.objects.create(
                patient=patient,
                name=medical_data["medicine"],
                dosage=medical_data["dosage"],
                frequency=medical_data["frequency"],
                doctor=medical_data["doctor"]
            )

        # -------------------------
        # Generate structured report
        # -------------------------

        if medical_data["document_type"] == "Lab Report":

            report = f"""Medical Document Report

Document Type:
Lab Report

Patient Information:
Patient Name: {medical_data["patient_name"]}
Patient ID: {medical_data["patient_id"]}
Age: {medical_data["age"]}
Gender: {medical_data["gender"]}

Report Information:
Report ID: {medical_data["report_id"]}
Collection Date: {medical_data["collection_date"]}
Report Date: {medical_data["report_date"]}

Laboratory Tests:
"""

            for test in medical_data["tests"]:

                report += (
                    f'Test: {test["test"]}\n'
                    f'Result: {test["result"]}\n'
                    f'Reference Range: {test["reference"]}\n\n'
                )

            report += """OCR Status:
Text successfully extracted from the uploaded document.
"""

        elif medical_data["document_type"] == "Prescription":

            report = f"""Medical Document Report

Document Type:
Prescription

Patient Information:
Patient Name: {medical_data["patient_name"]}

Prescription Information:
Medicine: {medical_data["medicine"]}
Dosage: {medical_data["dosage"]}
Frequency: {medical_data["frequency"]}
Doctor: {medical_data["doctor"]}
Diagnosis: {medical_data["diagnosis"]}

OCR Status:
Text successfully extracted from the uploaded document.
"""

        else:

            report = f"""Medical Document Report

Document Type:
Unknown

Patient Information:
Patient Name: {medical_data["patient_name"]}

Extracted Information:
Medicine: {medical_data["medicine"]}
Dosage: {medical_data["dosage"]}
Frequency: {medical_data["frequency"]}
Doctor: {medical_data["doctor"]}
Diagnosis: {medical_data["diagnosis"]}

OCR Status:
Text successfully extracted from the uploaded document.
"""

        # -------------------------
        # Store generated report
        # -------------------------

        document.report = report

        document.save(
            update_fields=[
                "extracted_text",
                "report",
                "document_type"
            ]
        )

        # -------------------------
        # Return response
        # -------------------------

        return JsonResponse(
            {
                "success": True,

                "filename": document.document_name,

                "text": text,

                "report": report,

                "document_id": document.id,

                "document_type": medical_data["document_type"],

                "medical_data": medical_data,
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
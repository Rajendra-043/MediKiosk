from django.http import JsonResponse
from django.views.decorators.http import require_POST

from patients.models import Patient, Medication, MedicalDocument

from .ocr_engine import (
    extract_text,
    extract_document_data
)
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
        # Run complete OCR
        # -------------------------

        ocr_data = extract_document_data(
            document.file.path
        )

        # Aligned text keeps columns (4 spaces for table gaps),
        # so tables do not collapse into a single stream.
        text = ocr_data.get("aligned_text") or ocr_data.get("text", "")

        # Fallback for legacy docs without aligned_text
        if not text:
            text = ocr_data.get("raw_text", "")

        layout = ocr_data.get("layout", {})
        segments = ocr_data.get("segments", [])

        # -------------------------
        # Store complete OCR data
        # -------------------------

        document.extracted_text = text

        # Save full spatial layout (rows + gaps + hierarchy) so
        # overlays and aligned-text rendering can use x/y.
        document.ocr_layout = layout

        document.ocr_segments = segments


        # -------------------------
        # Existing medical parser
        # -------------------------
        # Keep this temporarily so the
        # existing medical functionality
        # continues working.

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

        # --------------------------------------------------
        # Generate universal document report
        # --------------------------------------------------

        report = f"""Medical Document Report

        Document Type:
        {medical_data["document_type"]}

        Patient Information:
        Patient Name: {medical_data["patient_name"]}
        Patient ID: {medical_data["patient_id"]}
        Age: {medical_data["age"]}
        Gender: {medical_data["gender"]}

        Doctor:
        {medical_data["doctor"]}

        Diagnosis:
        {medical_data["diagnosis"]}

        Medicine:
        {medical_data["medicine"]}

        Dosage:
        {medical_data["dosage"]}

        Frequency:
        {medical_data["frequency"]}

        Report ID:
        {medical_data["report_id"]}

        Collection Date:
        {medical_data["collection_date"]}

        Report Date:
        {medical_data["report_date"]}

        """

        # --------------------------------------------------
        # Laboratory information
        # --------------------------------------------------

        if medical_data["tests"]:

            report += "Laboratory Tests:\n\n"

            for test in medical_data["tests"]:

                report += (
                    f'Test: {test["test"]}\n'
                    f'Result: {test["result"]}\n'
                    f'Reference Range: {test["reference"]}\n\n'
                )


        # --------------------------------------------------
        # Universal document segments
        # --------------------------------------------------

        report += "Document Segments:\n\n"

        for segment in medical_data["segments"]:

            report += (
                f'[{segment["heading"]}]\n'
            )

            for line in segment["content"]:

                report += (
                    f"{line}\n"
                )

            report += "\n"


        # --------------------------------------------------
        # OCR status
        # --------------------------------------------------

        report += """OCR Status:
        Text successfully extracted from the uploaded document.
        """

        # -------------------------
        # Store generated report
        # -------------------------

        document.report = report

        document.save(
            update_fields=[
                "extracted_text",
                "ocr_layout",
                "ocr_segments",
                "report",
                "document_type",
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

                # Structured information
                "medical_data": medical_data,

                # Human-readable report
                "report": report,

                # Document information
                "document_id": document.id,
                "document_type": medical_data["document_type"],
                # Spatial layout so frontend can render aligned columns
                "layout": layout,
                "image_width": ocr_data.get("image_width"),
                "image_height": ocr_data.get("image_height"),
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


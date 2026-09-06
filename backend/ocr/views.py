from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .ocr_engine import extract_text


@require_POST
def process_document(request):
    """
    Receive an uploaded medical document
    and extract text using OCR.
    """

    uploaded_file = request.FILES.get("document")

    if not uploaded_file:
        return JsonResponse(
            {
                "success": False,
                "error": "No document was uploaded."
            },
            status=400
        )

    # Supported image formats
    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
    }

    filename = uploaded_file.name.lower()

    if "." not in filename:
        return JsonResponse(
            {
                "success": False,
                "error": "File has no extension."
            },
            status=400
        )

    extension = "." + filename.rsplit(".", 1)[1]

    if extension not in allowed_extensions:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Unsupported file type. "
                    "Please upload JPG, PNG, WEBP, BMP, "
                    "TIFF or TIF."
                )
            },
            status=400
        )

    # Save uploaded file temporarily
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    )

    try:

        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)

        temp_file.close()

        # Run OCR
        extracted_text = extract_text(
            temp_file.name
        )

        return JsonResponse(
            {
                "success": True,
                "filename": uploaded_file.name,
                "text": extracted_text,
            }
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "error": str(error)
            },
            status=500
        )

    finally:

        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
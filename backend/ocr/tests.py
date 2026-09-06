from django.test import TestCase
import pytesseract
from PIL import Image, ImageDraw
from patients.models import Patient, MedicalDocument
from .data_extractor import extract_medical_data


from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

import io



# Tell pytesseract exactly where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class OCRTest(TestCase):

    def test_ocr_reads_text(self):

        # Create a temporary test image
        image = Image.new(
            "RGB",
            (800, 300),
            "white"
        )

        draw = ImageDraw.Draw(image)

        draw.text(
            (50, 50),
            "Patient Name: Rahul",
            fill="black"
        )

        draw.text(
            (50, 120),
            "Medicine: Paracetamol 500 mg",
            fill="black"
        )

        draw.text(
            (50, 190),
            "Dosage: Twice Daily",
            fill="black"
        )

        # Run OCR
        text = pytesseract.image_to_string(image)

        print("\n========== OCR RESULT ==========\n")
        print(text)
        print("\n================================\n")

        # Basic verification
        self.assertIn(
            "Patient",
            text
        )

        self.assertIn(
            "Paracetamol",
            text
        )





        self.assertIn(
            "Dosage",
            text
        )

        self.assertIn(
            "Twice Daily",
            text
        )













class OCRViewTest(TestCase):

    def test_upload_document(self):





        
        # -------------------------
        # Create test patient
        # -------------------------

        patient = Patient.objects.create(
            patient_id="TEST001",
            name="Rahul",
            gender="Male"
        )

        # -------------------------
        # Log patient into session
        # -------------------------

        session = self.client.session

        session["patient_id"] = patient.id

        session.save()

        # -------------------------
        # Create test image
        # ------------------











        # Create test image
        image = Image.new(
            "RGB",
            (800, 300),
            "white"
        )

        draw = ImageDraw.Draw(image)

        draw.text(
            (50, 50),
            "Patient Name: Rahul",
            fill="black"
        )

        draw.text(
            (50, 120),
            "Medicine: Paracetamol 500 mg",
            fill="black"
        )

        draw.text(
            (50, 190),
            "Dosage: Twice Daily",
            fill="black"
        )

        # Save image into memory
        image_buffer = io.BytesIO()

        image.save(
            image_buffer,
            format="PNG"
        )

        image_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            "test_document.png",
            image_buffer.read(),
            content_type="image/png"
        )

        # Send file to OCR endpoint
        response = self.client.post(
            "/ocr/process/",
            {
                "document": uploaded_file
            }
        )

        # Print response
        print("\n========== OCR VIEW RESPONSE ==========\n")
        print("STATUS:", response.status_code)
        print("CONTENT TYPE:", response.get("Content-Type"))
        print("CONTENT:")
        print(response.content.decode("utf-8", errors="replace"))
        print("\n=======================================\n")

        # Verify request succeeded
        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertTrue(
            data["success"]
        )

        self.assertIn(
            "Patient",
            data["text"]
        )

        self.assertIn(
            "Paracetamol",
            data["text"]
        )

        self.assertIn(
            "Dosage",
            data["text"]
        )

        self.assertIn(
            "Twice Daily",
            data["text"]
        )







class MedicalDataExtractionTest(TestCase):

    def test_extract_medical_data(self):

        text = """
        Patient Name: Rahul
        Medicine: Paracetamol 500 mg
        Dosage: Twice Daily
        """

        data = extract_medical_data(text)

        print("\n========== STRUCTURED DATA ==========\n")
        print(data)
        print("\n=====================================\n")

        self.assertEqual(
            data["patient_name"],
            "Rahul"
        )

        self.assertEqual(
            data["medicine"],
            "Paracetamol"
        )

        self.assertEqual(
            data["dosage"],
            "500 mg"
        )

        self.assertEqual(
            data["frequency"],
            "Twice Daily"
        )        
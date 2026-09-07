import os

import cv2
import numpy as np
import pytesseract
from PIL import Image
import re

# --------------------------------------------------
# Tesseract installation
# --------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# --------------------------------------------------
# Image preprocessing
# --------------------------------------------------

def preprocess_image(image):
    """
    Prepare an image before sending it to Tesseract.
    """

    image = np.array(image)

    # Convert RGB/RGBA image to grayscale
    if len(image.shape) == 3:

        if image.shape[2] == 4:
            gray = cv2.cvtColor(
                image,
                cv2.COLOR_RGBA2GRAY
            )
        else:
            gray = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2GRAY
            )

    else:
        gray = image


    # --------------------------------------------------
    # Upscale image
    # --------------------------------------------------

    height, width = gray.shape

    scale = 2

    gray = cv2.resize(
        gray,
        (width * scale, height * scale),
        interpolation=cv2.INTER_CUBIC
    )


    # --------------------------------------------------
    # Reduce noise
    # --------------------------------------------------

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )


    # --------------------------------------------------
    # Improve contrast
    # --------------------------------------------------

    gray = cv2.normalize(
        gray,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )


    # --------------------------------------------------
    # Adaptive threshold
    # --------------------------------------------------

    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )


    return processed


# --------------------------------------------------
# OCR
# --------------------------------------------------

def extract_text_from_image(file_path):
    """
    Extract text from an image file.
    """

    image = Image.open(file_path)

    # Convert image to RGB
    image = image.convert("RGB")

    processed_image = preprocess_image(image)


    # --------------------------------------------------
    # Tesseract OCR
    # --------------------------------------------------

    text = pytesseract.image_to_string(
        processed_image,
        config="--oem 3 --psm 6"
    )


    return text.strip()


# --------------------------------------------------
# Main OCR function
# --------------------------------------------------

def extract_text(file_path):
    """
    Main OCR function.
    """

    extension = os.path.splitext(
        file_path
    )[1].lower()


    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
    }


    if extension in image_extensions:

        return extract_text_from_image(
            file_path
        )


    raise ValueError(
        f"Unsupported file type: {extension}"
    )


# --------------------------------------------------
# Medical data extraction
# --------------------------------------------------




def clean_ocr_lines(text):
    """
    Clean OCR text while preserving the original order.
    """

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Remove excessive spaces
        line = re.sub(r"\s+", " ", line)

        lines.append(line)

    return lines


def extract_medical_data(text):
    """
    Extract useful medical information from OCR text.

    The original OCR text is not modified.
    """

    lines = clean_ocr_lines(text)

    data = {
        "patient_name": "",
        "medicine": "",
        "dosage": "",
        "frequency": "",
        "doctor": "",
        "diagnosis": "",
        "tests": [],
    }

    for line in lines:

        lower_line = line.lower()

        # ------------------------------------------
        # Patient name
        # ------------------------------------------

        match = re.search(
            r"(?:patient\s*name|name)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["patient_name"] = match.group(1).strip()
            continue


        # ------------------------------------------
        # Doctor
        # ------------------------------------------

        match = re.search(
            r"(?:doctor|dr\.?|referred\s*by)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["doctor"] = match.group(1).strip()
            continue


        # ------------------------------------------
        # Medicine
        # ------------------------------------------

        match = re.search(
            r"(?:medicine|medication|drug)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            medicine_value = match.group(1).strip()

            # Remove dosage from medicine name
            medicine_value = re.sub(
                r"\s*\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|%)(?:\b|$)",
                "",
                medicine_value,
                flags=re.IGNORECASE
            )

            data["medicine"] = medicine_value.strip()
            continue


        # ------------------------------------------
        # Dosage
        # ------------------------------------------

        match = re.search(
            r"(?:dosage|dose)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            dosage_value = match.group(1).strip()

            # Example:
            # 500 mg
            # 250 mg
            # 5 ml

            dosage_match = re.search(
                r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|tablet|tablets|capsule|capsules)",
                dosage_value,
                re.IGNORECASE
            )

            if dosage_match:
                data["dosage"] = dosage_match.group(0).strip()
            else:
                data["dosage"] = dosage_value

            continue


        # ------------------------------------------
        # Frequency
        # ------------------------------------------

        match = re.search(
            r"(?:frequency|freq)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["frequency"] = match.group(1).strip()
            continue


        # ------------------------------------------
        # Diagnosis
        # ------------------------------------------

        match = re.search(
            r"(?:diagnosis|diagnosed\s*with|condition)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["diagnosis"] = match.group(1).strip()
            continue


        # ------------------------------------------
        # Laboratory test lines
        # ------------------------------------------

        # Keep lines that look like:
        #
        # Haemoglobin 15 13-17 g/dL
        # Total Leucocyte Count 5000 4000-10000 /cumm
        # Neutrophils 50 40-80 %

        test_match = re.search(
            r"^(.+?)\s+"
            r"(\d+(?:\.\d+)?)\s+"
            r"(.+)$",
            line
        )

        if test_match:

            test_name = test_match.group(1).strip()
            result = test_match.group(2).strip()
            remaining = test_match.group(3).strip()

            # Avoid treating ordinary patient/medical lines as tests
            if len(test_name) > 2:

                data["tests"].append({
                    "test": test_name,
                    "result": result,
                    "reference": remaining
                })


    return data
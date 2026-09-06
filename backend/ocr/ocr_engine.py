import os

import cv2
import numpy as np
import pytesseract
from PIL import Image


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
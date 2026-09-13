import re


# ============================================================
# BASIC OCR LINE CLEANING
# ============================================================

def clean_ocr_lines(text):
    """
    Clean OCR lines while preserving their original order.
    """

    if not text:
        return []

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Normalize tabs and repeated spaces
        line = re.sub(r"\s+", " ", line)

        lines.append(line)

    return lines


# ============================================================
# DOCUMENT TYPE DETECTION
# ============================================================

def detect_document_type(text):
    """
    Detect the broad type of document.

    This does NOT modify OCR text.
    """

    lower = (text or "").lower()

    # --------------------------------------------------------
    # Lab reports first
    # --------------------------------------------------------

    if any(
        word in lower
        for word in [
            "complete blood count",
            "haematology",
            "hematology",
            "laboratory",
            "lab report",
            "test description",
            "reference range",
            "cbc",
            "blood test",
            "blood report",
        ]
    ):
        return "Lab Report"

    # --------------------------------------------------------
    # Prescription
    # --------------------------------------------------------

    if any(
        word in lower
        for word in [
            "prescription",
            "medicine",
            "medication",
            "tablet",
            "tablets",
            "capsule",
            "capsules",
            "dosage",
            "dose",
            "frequency",
        ]
    ):
        return "Prescription"

    # --------------------------------------------------------
    # Registration / application forms
    # --------------------------------------------------------

    if any(
        word in lower
        for word in [
            "registration form",
            "application form",
            "registration",
            "student",
            "school",
            "college",
            "admission",
            "enrollment",
            "date of birth",
        ]
    ):
        return "Form / Registration Document"

    # --------------------------------------------------------
    # Invoice / bill
    # --------------------------------------------------------

    if any(
        word in lower
        for word in [
            "invoice",
            "invoice number",
            "bill number",
            "billing",
            "amount due",
            "subtotal",
            "grand total",
            "total amount",
        ]
    ):
        return "Invoice / Bill"

    # --------------------------------------------------------
    # Certificate
    # --------------------------------------------------------

    if any(
        word in lower
        for word in [
            "certificate",
            "certification",
            "this is to certify",
            "issued on",
        ]
    ):
        return "Certificate"

    # --------------------------------------------------------
    # General document
    # --------------------------------------------------------

    return "General Document"


# ============================================================
# SEGMENT EXTRACTION
# ============================================================

def extract_segments(text):
    """
    Divide OCR text into readable sections.

    The original OCR text is not changed.
    """

    lines = clean_ocr_lines(text)

    segments = []

    current_heading = ""
    current_content = []

    def save_segment():

        nonlocal current_heading
        nonlocal current_content

        if current_heading or current_content:

            segments.append(
                {
                    "heading": current_heading,
                    "content": current_content,
                }
            )

        current_heading = ""
        current_content = []

    for line in lines:

        stripped = line.strip()

        # ----------------------------------------------------
        # Obvious headings
        # ----------------------------------------------------

        is_upper_heading = (
            len(stripped) < 100
            and stripped.upper() == stripped
            and any(char.isalpha() for char in stripped)
        )

        is_colon_heading = (
            stripped.endswith(":")
            and len(stripped) < 100
        )

        # ----------------------------------------------------
        # Known section headings
        # ----------------------------------------------------

        lower = stripped.lower()

        known_heading = any(
            heading in lower
            for heading in [
                "patient information",
                "prescription information",
                "report information",
                "laboratory tests",
                "hematology",
                "haematology",
                "complete blood count",
                "differential leucocyte count",
                "rbc indices",
                "platelets indices",
                "interpretation",
                "student information",
                "personal information",
                "invoice details",
                "billing information",
            ]
        )

        is_heading = (
            is_upper_heading
            or is_colon_heading
            or known_heading
        )

        # ----------------------------------------------------
        # Start a new segment
        # ----------------------------------------------------

        if is_heading:

            if current_heading or current_content:
                save_segment()

            current_heading = stripped

        else:

            if not current_heading:

                # First line becomes heading only when
                # there is no active segment.
                current_heading = stripped

            else:

                current_content.append(stripped)

    # Save final segment

    save_segment()

    return segments


# ============================================================
# HELPERS
# ============================================================

def first_match(patterns, text, flags=re.IGNORECASE):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags
        )

        if match:
            return match

    return None


def clean_value(value):
    """
    Clean a field value without destroying useful content.
    """

    if not value:
        return ""

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip(" :-")


def extract_value_after_label(
    line,
    labels
):
    """
    Extract:

    Name: Rahul

    Patient Name - Rahul
    """

    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )

    match = re.search(
        rf"(?:{label_pattern})\s*[:\-]\s*(.+)",
        line,
        re.IGNORECASE
    )

    if not match:
        return ""

    return clean_value(
        match.group(1)
    )


# ============================================================
# MEDICAL INFORMATION EXTRACTION
# ============================================================

def extract_medical_data(text):

    lines = clean_ocr_lines(text)

    document_type = detect_document_type(text)

    data = {

        # Document
        "document_type": document_type,

        # Patient
        "patient_name": "",
        "patient_id": "",
        "age": "",
        "gender": "",

        # Prescription
        "medicine": "",
        "dosage": "",
        "frequency": "",
        "doctor": "",
        "diagnosis": "",

        # Lab report
        "report_id": "",
        "collection_date": "",
        "report_date": "",

        # Laboratory tests
        "tests": [],

        # Generic OCR organization
        "segments": extract_segments(text),

        # Original OCR
        "raw_text": text or "",
    }

    # ========================================================
    # UNIVERSAL FIELD EXTRACTION
    # ========================================================

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # ------------------------------------------
        # Patient Name
        # ------------------------------------------

        match = re.search(
            r"patient\s*name\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["patient_name"] = match.group(1).strip()
            continue

        # ------------------------------------------
        # Age / Gender
        # ------------------------------------------

        match = re.search(
            r"age\s*/?\s*gender\s*[:\-]\s*(\d+)\s*/\s*([A-Za-z]+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["age"] = match.group(1).strip()
            data["gender"] = match.group(2).strip()
            continue

        # ------------------------------------------
        # Report ID
        # ------------------------------------------

        match = re.search(
            r"report\s*id\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["report_id"] = match.group(1).strip()
            continue

        # ------------------------------------------
        # Collection Date
        # ------------------------------------------

        match = re.search(
            r"collection\s*date\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["collection_date"] = match.group(1).strip()
            continue

        # ------------------------------------------
        # Report Date
        # ------------------------------------------

        match = re.search(
            r"report\s*date\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["report_date"] = match.group(1).strip()
            continue

    # ------------------------------------------
    # YOUR EXISTING TEST DETECTION CODE
    # ------------------------------------------

    # test parsing comes AFTER Age / Gender

         # ------------------------------------------
        # Skip Age / Gender from laboratory tests
        # ------------------------------------------

        if re.match(
            r"age\s*/\s*gender",
            line,
            re.IGNORECASE
        ):
            continue   




        # ----------------------------------------------------
        # Standalone age
        # ----------------------------------------------------

        match = re.search(
            r"\bage\s*[:\-]\s*(\d{1,3})\b",
            line,
            re.IGNORECASE
        )

        if match and not data["age"]:

            data["age"] = match.group(1)

        # ----------------------------------------------------
        # Gender
        # ----------------------------------------------------

        match = re.search(
            r"\b(male|female)\b",
            line,
            re.IGNORECASE
        )

        if match and not data["gender"]:

            data["gender"] = (
                "Male"
                if match.group(1).lower() == "male"
                else "Female"
            )

        # ----------------------------------------------------
        # Doctor / Referred By
        # ----------------------------------------------------

        match = re.search(
            r"(?:doctor|dr\.?|referred\s+by)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match and not data["doctor"]:

            value = clean_value(
                match.group(1)
            )

            value = re.split(
                r"\s+(?:collection\s+date|report\s+date|"
                r"phone\s+no|patient\s+id)\b",
                value,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0]

            data["doctor"] = clean_value(
                value
            )

        # ----------------------------------------------------
        # Diagnosis
        # ----------------------------------------------------

        match = re.search(
            r"(?:diagnosis|diagnosed\s+with|condition)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match and not data["diagnosis"]:

            data["diagnosis"] = clean_value(
                match.group(1)
            )

        # ----------------------------------------------------
        # Report ID
        # ----------------------------------------------------

        match = re.search(
            r"(?:report\s+id|report\s+no\.?)"
            r"\s*[:\-]?\s*"
            r"([A-Za-z0-9][A-Za-z0-9\-_\/]*)",
            line,
            re.IGNORECASE
        )

        if match and not data["report_id"]:

            data["report_id"] = clean_value(
                match.group(1)
            )

        # ----------------------------------------------------
        # Collection Date
        # ----------------------------------------------------

        match = re.search(
            r"(?:collection\s+date|sample\s+collection)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match and not data["collection_date"]:

            value = clean_value(
                match.group(1)
            )

            value = re.split(
                r"\s+(?:report\s+date|phone\s+no)\b",
                value,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0]

            data["collection_date"] = clean_value(
                value
            )

        # ----------------------------------------------------
        # Report Date
        # ----------------------------------------------------

        match = re.search(
            r"(?:report\s+date|reported\s+on)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match and not data["report_date"]:

            value = clean_value(
                match.group(1)
            )

            data["report_date"] = value

        # ----------------------------------------------------
        # Medicine
        # ----------------------------------------------------

        match = re.search(
            r"(?:medicine|medication|drug)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match and not data["medicine"]:

            value = clean_value(
                match.group(1)
            )

            # Detect dosage inside medicine field
            dose_match = re.search(
                r"\b\d+(?:\.\d+)?\s*"
                r"(?:mg|mcg|g|ml|tablet|tablets|"
                r"capsule|capsules)\b",
                value,
                re.IGNORECASE
            )

            if dose_match:

                if not data["dosage"]:
                    data["dosage"] = (
                        dose_match.group(0)
                        .strip()
                    )

                value = (
                    value[:dose_match.start()]
                    + value[dose_match.end():]
                )

            data["medicine"] = clean_value(
                value
            )

        # ----------------------------------------------------
        # Dosage
        # ----------------------------------------------------

        match = re.search(
            r"(?:dosage|dose)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            dosage_value = clean_value(
                match.group(1)
            )

            dosage_match = re.search(
                r"\b\d+(?:\.\d+)?\s*"
                r"(?:mg|mcg|g|ml|"
                r"tablet|tablets|capsule|capsules)\b",
                dosage_value,
                re.IGNORECASE
            )

            if dosage_match:

                data["dosage"] = (
                    dosage_match.group(0)
                    .strip()
                )

            elif not data["frequency"]:

                # Some OCR documents incorrectly label
                # frequency as dosage.
                if any(
                    word in dosage_value.lower()
                    for word in [
                        "daily",
                        "twice",
                        "once",
                        "morning",
                        "evening",
                        "night",
                        "hourly",
                    ]
                ):
                    data["frequency"] = dosage_value

                else:
                    data["dosage"] = dosage_value

        # ----------------------------------------------------
        # Frequency
        # ----------------------------------------------------

        match = re.search(
            r"(?:frequency|freq)"
            r"\s*[:\-]\s*"
            r"(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            data["frequency"] = clean_value(
                match.group(1)
            )





        # ------------------------------------------
        # Ignore Age / Gender from laboratory tests
        # ------------------------------------------

        if re.match(
            r"age\s*/?\s*gender",
            line,
            re.IGNORECASE
        ):
            continue





    # ========================================================
    # LABORATORY TEST EXTRACTION
    # ========================================================

    # Common headings that should never become tests
    ignored_test_names = {
        "test description",
        "test",
        "description",
        "result",
        "reference range",
        "unit",
        "laboratory tests",
        "patient information",
        "report information",
    }

    for line in lines:

        # ----------------------------------------------------
        # Skip obvious headings
        # ----------------------------------------------------

        lower_line = line.lower().strip()

        if lower_line in ignored_test_names:
            continue

        if lower_line.startswith(
            (
                "name :",
                "patient name:",
                "patient id:",
                "age/gender:",
                "report id:",
                "collection date:",
                "report date:",
                "phone no:",
                "referred by:",
                "medicine:",
                "dosage:",
                "frequency:",
                "doctor:",
                "diagnosis:",
            )
        ):
            continue

        # ----------------------------------------------------
        # Normal lab format:
        #
        # Haemoglobin 15 13-17 g/dL
        #
        # Test name can contain spaces.
        # ----------------------------------------------------

        match = re.match(
            r"^(.+?)\s+"
            r"(-?\d+(?:\.\d+)?)\s+"
            r"(.+)$",
            line
        )

        if not match:
            continue

        test_name = clean_value(
            match.group(1)
        )

        result = clean_value(
            match.group(2)
        )

        remaining = clean_value(
            match.group(3)
        )

        # ----------------------------------------------------
        # Prevent ordinary text from becoming tests
        # ----------------------------------------------------

        if len(test_name) < 3:
            continue

        if test_name.lower() in ignored_test_names:
            continue

        if any(
            word in test_name.lower()
            for word in [
                "patient information",
                "prescription information",
                "report information",
                "ocr status",
                "medicine",
                "dosage",
                "frequency",
                "doctor",
                "diagnosis",
            ]
        ):
            continue

        # ----------------------------------------------------
        # Separate reference range and unit where possible
        # ----------------------------------------------------

        reference = remaining
        unit = ""

        unit_match = re.search(
            r"\s+"
            r"((?:mg|mcg|g|kg|ml|"
            r"g/dl|mg/dl|fl|pg|"
            r"%|/cumm|/mm3|/eumm|"
            r"cells/ul|cells/µl|"
            r"u/l|iu/l|bpm))"
            r"\s*$",
            remaining,
            re.IGNORECASE
        )

        if unit_match:

            unit = unit_match.group(1).strip()

            reference = clean_value(
                remaining[
                    :unit_match.start()
                ]
            )

        # ----------------------------------------------------
        # Ignore lines that are clearly not tests
        # ----------------------------------------------------

        if test_name.lower() in [
            "absolute leucocyte count",
            "absolute leukocyte count",
        ] and not reference:

            # Keep it only if it has useful content
            continue

        data["tests"].append(
            {
                "test": test_name,
                "result": result,
                "reference": reference,
                "unit": unit,
            }
        )

    # ========================================================
    # REMOVE DUPLICATE TESTS
    # ========================================================

    unique_tests = []

    seen = set()

    for test in data["tests"]:

        key = (
            test["test"].lower(),
            test["result"],
            test["reference"].lower(),
        )

        if key in seen:
            continue

        seen.add(key)

        unique_tests.append(test)

    data["tests"] = unique_tests

    # ========================================================
    # FINAL DOCUMENT TYPE FALLBACK
    # ========================================================

    if not data["document_type"]:

        data["document_type"] = "General Document"

    return data
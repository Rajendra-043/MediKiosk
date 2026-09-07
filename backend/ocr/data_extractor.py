import re


def clean_lines(text):
    """
    Clean OCR text while preserving the original order.
    """
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        line = re.sub(r"\s+", " ", line)

        lines.append(line)

    return lines


def extract_medical_data(text):
    """
    Extract structured medical information from OCR text.

    Supports:
    - Lab reports
    - Prescriptions
    - Basic medical documents
    """

    lines = clean_lines(text)

    data = {
        "document_type": "Unknown",

        "patient_name": "",
        "patient_id": "",
        "age": "",
        "gender": "",

        "medicine": "",
        "dosage": "",
        "frequency": "",

        "doctor": "",
        "diagnosis": "",

        "report_id": "",
        "collection_date": "",
        "report_date": "",

        "tests": [],
    }

    # ==================================================
    # DOCUMENT TYPE
    # ==================================================

    full_text = " ".join(lines).lower()

    lab_keywords = [
        "haematology",
        "hematology",
        "complete blood count",
        "cbc",
        "test description",
        "reference range",
        "haemoglobin",
        "hemoglobin",
        "total leucocyte count",
        "platelet count",
    ]

    prescription_keywords = [
        "medicine",
        "medication",
        "dosage",
        "dose",
        "frequency",
        "tablet",
        "capsule",
        "prescription",
    ]

    lab_score = sum(
        1 for keyword in lab_keywords
        if keyword in full_text
    )

    prescription_score = sum(
        1 for keyword in prescription_keywords
        if keyword in full_text
    )

    if lab_score >= 2:
        data["document_type"] = "Lab Report"

    elif prescription_score >= 2:
        data["document_type"] = "Prescription"


    # ==================================================
    # PATIENT NAME
    # ==================================================

    for line in lines:

        # Normal format:
        # Patient Name: Rahul
        match = re.search(
            r"(?:patient\s*name)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            value = match.group(1).strip()

            # Remove possible extra fields
            value = re.split(
                r"\s+(?:patient\s*id|age|gender)\b",
                value,
                flags=re.IGNORECASE
            )[0].strip()

            data["patient_name"] = value
            break


    # Lab report format:
    # Name : MrDummy Patient ID 2 PN2

    if not data["patient_name"]:

        for line in lines:

            match = re.search(
                r"\bName\s*:\s*(.+?)\s+Patient\s*ID\b",
                line,
                re.IGNORECASE
            )

            if match:
                data["patient_name"] = match.group(1).strip()
                break


    # ==================================================
    # PATIENT ID
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:patient\s*id|patient\s*no)\s*[:\-]?\s*(.+?)(?=\s+(?:Age|Gender|Report|Referred|Collection)\b|$)",
            line,
            re.IGNORECASE
        )

        if match:
            data["patient_id"] = match.group(1).strip()
            break


    # Special lab format:
    # Name : MrDummy Patient ID 2 PN2

    if not data["patient_id"]:

        for line in lines:

            match = re.search(
                r"Patient\s*ID\s*[:\-]?\s*(.+?)(?=\s+(?:Age|Gender|Report|Referred|Collection)\b|$)",
                line,
                re.IGNORECASE
            )

            if match:
                data["patient_id"] = match.group(1).strip()
                break


    # ==================================================
    # AGE + GENDER
    # ==================================================

    for line in lines:

        # Example:
        # Age/Gender : 20/Male

        match = re.search(
            r"Age\s*/\s*Gender\s*[:\-]?\s*(\d+)\s*/\s*(Male|Female|M|F|Other)",
            line,
            re.IGNORECASE
        )

        if match:

            data["age"] = match.group(1)

            gender = match.group(2).lower()

            if gender == "m":
                gender = "Male"

            elif gender == "f":
                gender = "Female"

            else:
                gender = gender.capitalize()

            data["gender"] = gender

            break


    # Normal separate Age field

    if not data["age"]:

        for line in lines:

            match = re.search(
                r"\bAge\s*[:\-]?\s*(\d+)",
                line,
                re.IGNORECASE
            )

            if match:
                data["age"] = match.group(1)
                break


    # Normal separate Gender field

    if not data["gender"]:

        for line in lines:

            match = re.search(
                r"\bGender\s*[:\-]?\s*(Male|Female|M|F|Other)",
                line,
                re.IGNORECASE
            )

            if match:

                gender = match.group(1).lower()

                if gender == "m":
                    gender = "Male"

                elif gender == "f":
                    gender = "Female"

                else:
                    gender = gender.capitalize()

                data["gender"] = gender
                break


    # ==================================================
    # DOCTOR / REFERRED BY
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Referred\s*By|Doctor|Dr\.?)\s*[:\-]\s*(.+?)(?=\s+(?:Collection|ReportDate|Report\s*Date|Phone)\b|$)",
            line,
            re.IGNORECASE
        )

        if match:

            data["doctor"] = match.group(1).strip()
            break


    # ==================================================
    # DIAGNOSIS
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Diagnosis|Diagnosed\s*With|Condition)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            data["diagnosis"] = match.group(1).strip()
            break


    # ==================================================
    # REPORT ID
    # ==================================================

    for line in lines:

        match = re.search(
            r"Report\s*ID\s*[:\-]?\s*(.+?)(?=\s+(?:Referred|Collection|ReportDate|Report\s*Date)\b|$)",
            line,
            re.IGNORECASE
        )

        if match:

            data["report_id"] = match.group(1).strip()
            break


    # ==================================================
    # COLLECTION DATE
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Collection\s*Date|Sample\s*Collection)\s*[:\-]\s*(.+?)(?=\s+(?:Phone|ReportDate|Report\s*Date)\b|$)",
            line,
            re.IGNORECASE
        )

        if match:

            data["collection_date"] = match.group(1).strip()
            break


    # ==================================================
    # REPORT DATE
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Report\s*Date|ReportDate|Reported\s*On)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            data["report_date"] = match.group(1).strip()
            break


    # ==================================================
    # MEDICINE
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Medicine|Medication|Drug)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            medicine_value = match.group(1).strip()

            dosage_match = re.search(
                r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|tablet|tablets|capsule|capsules)",
                medicine_value,
                re.IGNORECASE
            )

            if dosage_match:

                data["dosage"] = dosage_match.group(0).strip()

                medicine_value = (
                    medicine_value[:dosage_match.start()]
                    +
                    medicine_value[dosage_match.end():]
                )

            data["medicine"] = medicine_value.strip()

            break


    # ==================================================
    # DOSAGE
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Dosage|Dose)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            dosage_match = re.search(
                r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|tablet|tablets|capsule|capsules)",
                value,
                re.IGNORECASE
            )

            if dosage_match:

                data["dosage"] = dosage_match.group(0).strip()

                remaining = value[
                    dosage_match.end():
                ].strip()

                if remaining:
                    data["frequency"] = remaining

            else:

                frequency_words = [
                    "once",
                    "twice",
                    "thrice",
                    "daily",
                    "weekly",
                    "morning",
                    "evening",
                    "night",
                    "hourly",
                    "every",
                ]

                if any(
                    word in value.lower()
                    for word in frequency_words
                ):
                    data["frequency"] = value

                else:
                    data["dosage"] = value

            break


    # ==================================================
    # FREQUENCY
    # ==================================================

    for line in lines:

        match = re.search(
            r"(?:Frequency|Freq)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            data["frequency"] = match.group(1).strip()
            break


    # ==================================================
    # LABORATORY TESTS
    # ==================================================

    if data["document_type"] == "Lab Report":

        test_names = [
            "Haemoglobin",
            "Hemoglobin",
            "Total Leucocyte Count",
            "Neutrophils",
            "Lymphocytes",
            "Eosinophils",
            "Monocytes",
            "Basophils",
            "Absolute Neutrophils",
            "Absolute Lymphocytes",
            "Absolute Eosinophils",
            "Absolute Monocytes",
            "RBC Count",
            "MCV",
            "MCH",
            "MCHC",
            "Hct",
            "HCT",
            "Het",
            "RDW-CV",
            "RDW-SD",
            "ROW-SD",
            "Platelet Count",
            "PCT",
            "MPV",
            "PDW",
        ]

        for line in lines:

            for test_name in test_names:

                if line.lower().startswith(
                    test_name.lower()
                ):

                    remaining = line[
                        len(test_name):
                    ].strip()

                    # Extract first numeric result
                    result_match = re.search(
                        r"(\d+(?:\.\d+)?)",
                        remaining
                    )

                    if not result_match:
                        continue

                    result = result_match.group(1)

                    reference = remaining[
                        result_match.end():
                    ].strip()

                    # Remove obvious OCR junk before reference
                    reference = re.sub(
                        r"^[^\d\-]*",
                        "",
                        reference
                    ).strip()

                    data["tests"].append({
                        "test": test_name,
                        "result": result,
                        "reference": reference,
                    })

                    break


    return data
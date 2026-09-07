import re


def clean_lines(text):
    """
    Clean OCR text while preserving its original order.
    """

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Replace multiple spaces with one
        line = re.sub(r"\s+", " ", line)

        lines.append(line)

    return lines


def extract_medical_data(text):
    """
    Convert raw OCR text into structured medical information.
    """

    lines = clean_lines(text)

    data = {
        "patient_name": "",
        "patient_id": "",
        "age": "",
        "gender": "",
        "doctor": "",
        "diagnosis": "",
        "medicine": "",
        "dosage": "",
        "frequency": "",
        "report_id": "",
        "collection_date": "",
        "report_date": "",
        "tests": [],
    }

    for line in lines:

        lower = line.lower()


        # ------------------------------------------
        # Patient Name
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
        # Patient ID
        # ------------------------------------------

        match = re.search(
            r"(?:patient\s*id|patient\s*no)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["patient_id"] = match.group(1).strip()
            continue


        # ------------------------------------------
        # Age / Gender
        # ------------------------------------------

        match = re.search(
            r"age\s*[/\-]?\s*gender\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            age_match = re.search(
                r"\d+",
                value
            )

            if age_match:
                data["age"] = age_match.group(0)

            gender_match = re.search(
                r"\b(male|female|m|f|other)\b",
                value,
                re.IGNORECASE
            )

            if gender_match:
                gender = gender_match.group(1)

                if gender.lower() == "m":
                    gender = "Male"

                elif gender.lower() == "f":
                    gender = "Female"

                data["gender"] = gender

            continue


        # ------------------------------------------
        # Doctor / Referred By
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
        # Report ID
        # ------------------------------------------

        match = re.search(
            r"(?:report\s*id|report\s*no)\s*[:\-]\s*(.+)",
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
            r"(?:collection\s*date|sample\s*collection)\s*[:\-]\s*(.+)",
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
            r"(?:report\s*date|reported\s*on)\s*[:\-]\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["report_date"] = match.group(1).strip()
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

            # Extract dose from medicine line if present
            dosage_match = re.search(
                r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml)",
                medicine_value,
                re.IGNORECASE
            )

            if dosage_match:

                data["dosage"] = dosage_match.group(0)

                medicine_value = (
                    medicine_value[:dosage_match.start()]
                    +
                    medicine_value[dosage_match.end():]
                )

            data["medicine"] = medicine_value.strip()

            continue


        # ------------------------------------------
        # Dosage / Frequency
        # ------------------------------------------

        match = re.search(
            r"(?:dosage|dose)\s*[:\-]\s*(.+)",
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

                data["dosage"] = dosage_match.group(0)

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
        # Laboratory Test
        # ------------------------------------------

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

            # Ignore obvious non-test lines
            ignored_words = [
                "phone",
                "email",
                "website",
                "patient",
                "report",
                "address",
            ]

            if not any(
                word in test_name.lower()
                for word in ignored_words
            ):

                data["tests"].append({
                    "test": test_name,
                    "result": result,
                    "reference": remaining,
                })


    return data
import re


def extract_medical_data(text):
    """
    Extract structured medical information
    from OCR text.

    Returns only information that can be
    confidently identified.
    """

    data = {
        "patient_name": "",
        "medicine": "",
        "dosage": "",
        "frequency": "",
        "doctor": "",
        "diagnosis": "",
    }

    if not text:
        return data

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:

        # -------------------------
        # Patient Name
        # -------------------------

        match = re.match(
            r"patient\s*name\s*:\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["patient_name"] = match.group(1).strip()
            continue


        # -------------------------
        # Medicine
        # -------------------------

        match = re.match(
            r"medicine\s*:\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            medicine_value = match.group(1).strip()

            # Try to separate medicine name
            # from dosage such as 500 mg.
            dosage_match = re.search(
                r"(.+?)\s+(\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|%))$",
                medicine_value,
                re.IGNORECASE
            )

            if dosage_match:
                data["medicine"] = (
                    dosage_match.group(1).strip()
                )

                if not data["dosage"]:
                    data["dosage"] = (
                        dosage_match.group(2).strip()
                    )

            else:
                data["medicine"] = medicine_value

            continue


       # -------------------------
        # Dosage
        # -------------------------

        match = re.match(
            r"dosage\s*:\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            dosage_value = match.group(1).strip()

            # Check whether this is actually a frequency
            frequency_match = re.fullmatch(
                r"(once|twice|thrice|\d+\s*times?)\s+"
                r"(daily|weekly|monthly)",
                dosage_value,
                re.IGNORECASE
            )

            if frequency_match:
                data["frequency"] = dosage_value

            else:
                data["dosage"] = dosage_value

            continue

        # -------------------------
        # Frequency
        # -------------------------

        match = re.match(
            r"(frequency|freq)\s*:\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["frequency"] = (
                match.group(2).strip()
            )
            continue


        # -------------------------
        # Doctor
        # -------------------------

        match = re.match(
            r"doctor(?:\s*name)?\s*:\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["doctor"] = (
                match.group(1).strip()
            )
            continue


        # -------------------------
        # Diagnosis
        # -------------------------

        match = re.match(
            r"diagnosis\s*:\s*(.+)",
            line,
            re.IGNORECASE
        )

        if match:
            data["diagnosis"] = (
                match.group(1).strip()
            )
            continue

    return data
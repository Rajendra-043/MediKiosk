"""ABHA demo helpers: validation, masking, generation.

Demo mode: no real ABDM/UIDAI call is made. Aadhaar numbers are validated
only for format + Verhoeff checksum, and only the last 4 digits are kept.
OTP is generated locally and shown on screen (no SMS gateway wired).
"""

import random
import re

# Verhoeff tables (used by Aadhaar and ABHA numbers)
_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 7, 2, 5],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_checksum(num_str):
    """Compute Verhoeff check digit for a numeric string (without check)."""
    c = 0
    for i, ch in enumerate(reversed(num_str)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


def verhoeff_validate(num_str):
    """Validate a full numeric string including its Verhoeff check digit."""
    if not num_str or not num_str.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(num_str)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def normalize_aadhaar(value):
    """Strip spaces/dashes from an Aadhaar entry."""
    return re.sub(r"[\s\-]", "", (value or "").strip())


def validate_aadhaar(value):
    """12 digits + Verhoeff checksum (format-level check only)."""
    num = normalize_aadhaar(value)
    if len(num) != 12 or not num.isdigit():
        return False, "Aadhaar number must be 12 digits."
    if num[0] in ("0", "1"):
        return False, "Aadhaar number looks invalid (cannot start with 0 or 1)."
    if not verhoeff_validate(num):
        return False, "Aadhaar number failed checksum validation."
    return True, ""


def mask_aadhaar(value):
    num = normalize_aadhaar(value)
    if len(num) != 12:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{num[-4:]}"


def normalize_abha_number(value):
    return re.sub(r"[\s\-]", "", (value or "").strip())


def validate_abha_number(value):
    num = normalize_abha_number(value)
    if len(num) != 14 or not num.isdigit():
        return False, "ABHA Number must be 14 digits."
    return True, ""


def validate_abha_address(value):
    addr = (value or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9._\-]{2,30}@abdm", addr):
        return False, (
            "ABHA Address must look like name@abdm "
            "(start with a letter, 4-32 chars before @abdm)."
        )
    return True, ""


def validate_mobile(value):
    mobile = re.sub(r"[\s\-+]", "", (value or "").strip())
    if mobile.startswith("91") and len(mobile) == 12:
        mobile = mobile[2:]
    if not re.fullmatch(r"[6-9]\d{9}", mobile):
        return False, "Mobile number must be a 10-digit Indian mobile number."
    return True, ""


def mask_mobile(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 4:
        return "XXXXXX XXXX"
    return f"XXXXXX {digits[-4:]}"


def suggest_abha_address(name):
    base = re.sub(r"[^a-z0-9._\-]", "", (name or "").strip().lower().replace(" ", "."))
    base = re.sub(r"\.+", ".", base).strip(".-") or "user"
    return f"{base[:28]}@abdm"


def generate_abha_number(exists_check):
    """Generate a unique 14-digit ABHA number with Verhoeff check digit."""
    for _ in range(50):
        first13 = f"{random.randint(10**12, 10**13 - 1)}"
        num = first13 + verhoeff_checksum(first13)
        if not exists_check(num):
            return num
    raise ValueError("Could not generate a unique ABHA number, please retry.")


def generate_otp():
    return f"{random.randint(100000, 999999)}"


def demo_profile_from_patient(patient):
    """Prefill Page-3 fields from the logged-in patient record."""
    return {
        "full_name": patient.name or "",
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else "",
        "gender": patient.gender or "",
        "mobile": patient.phone or "",
    }

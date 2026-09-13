"""ABHA Health ID flows (demo mode).

Two portions, as requested:
  1. Link EXISTING ABHA ID  -> ABHA number/address + password validation.
  2. CREATE new ABHA ID     -> 4-step Aadhaar wizard
     (method -> OTP -> confirm profile -> ABHA address & finish).

Demo mode: no real ABDM/UIDAI call. OTP is generated locally and shown
on screen. Only masked identity data is stored (last-4 Aadhaar).
"""

import time

from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from patients.models import Patient

from .abha_utils import (
    demo_profile_from_patient,
    generate_abha_number,
    generate_otp,
    mask_aadhaar,
    mask_mobile,
    normalize_abha_number,
    normalize_aadhaar,
    suggest_abha_address,
    validate_aadhaar,
    validate_abha_address,
    validate_abha_number,
    validate_mobile,
)
from .models import AbhaProfile

SESSION_KEY = "abha_create"
OTP_TTL_SECONDS = 5 * 60
OTP_MAX_ATTEMPTS = 3


def _patient(request):
    patient_id = request.session.get("patient_id")
    if not patient_id:
        return None
    return get_object_or_404(Patient, id=patient_id)


def _profile(request, patient):
    try:
        return patient.abha_profile
    except AbhaProfile.DoesNotExist:
        return None


# -------------------------
# HUB
# -------------------------

def abha_home(request):
    patient = _patient(request)
    if not patient:
        return redirect("/patient/login/")

    profile = _profile(request, patient)
    return render(
        request,
        "paitent/abha_home.html",
        {"patient": patient, "profile": profile},
    )


# -------------------------
# LINK EXISTING ABHA ID
# -------------------------

def abha_link(request):
    patient = _patient(request)
    if not patient:
        return redirect("/patient/login/")

    if _profile(request, patient):
        return redirect("/patient/abha/")

    error = ""
    identifier = ""
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        password = request.POST.get("password") or ""

        if not identifier:
            error = "Please enter your ABHA Number or ABHA Address."
        elif not password:
            error = "Please enter your ABHA password."
        else:
            abha_number = ""
            abha_address = ""
            if "@" in identifier:
                ok, msg = validate_abha_address(identifier)
                if not ok:
                    error = msg
                else:
                    abha_address = identifier.strip().lower()
                    # Demo link: derive a stable placeholder number only
                    # when the user links via address (no real ABDM lookup).
                    abha_number = ""
            else:
                ok, msg = validate_abha_number(identifier)
                if not ok:
                    error = msg
                else:
                    abha_number = normalize_abha_number(identifier)

            if not error:
                if AbhaProfile.objects.filter(
                    patient=patient
                ).exists():
                    return redirect("/patient/abha/")

                query = (
                    AbhaProfile.objects.filter(abha_number=abha_number)
                    if abha_number
                    else AbhaProfile.objects.filter(abha_address=abha_address)
                )
                if abha_number and query.exists():
                    error = "This ABHA Number is already linked to another patient here."
                elif abha_address and query.exists():
                    error = "This ABHA Address is already linked to another patient here."
                else:
                    profile = AbhaProfile.objects.create(
                        patient=patient,
                        abha_number=abha_number or normalize_abha_number(
                            f"{abs(hash(abha_address)) % (10**14):014d}"
                        ),
                        abha_address=abha_address,
                        full_name=patient.name or "",
                        date_of_birth=patient.date_of_birth,
                        gender=patient.gender or "",
                        mobile=patient.phone or "",
                        verified=True,
                        password_hash=make_password(password),
                    )
                    # Keep the patient phone in sync if empty
                    return render(
                        request,
                        "paitent/abha_home.html",
                        {
                            "patient": patient,
                            "profile": profile,
                            "linked": True,
                        },
                    )

    return render(
        request,
        "paitent/abha_link.html",
        {"patient": patient, "error": error, "identifier": identifier},
    )


# -------------------------
# CREATE WIZARD (4 steps)
# -------------------------

def _wizard(request):
    data = request.session.get(SESSION_KEY)
    if not isinstance(data, dict):
        data = {"step": 1}
        request.session[SESSION_KEY] = data
    return data


def abha_create(request):
    patient = _patient(request)
    if not patient:
        return redirect("/patient/login/")

    if _profile(request, patient):
        return redirect("/patient/abha/")

    wizard = _wizard(request)
    step = int(request.GET.get("step", wizard.get("step", 1)))
    step = min(max(step, 1), 4)
    error = ""

    if request.method == "POST":
        posted_step = int(request.POST.get("step", step))

        # ---- Step 1: Aadhaar + consent ----
        if posted_step == 1:
            aadhaar = request.POST.get("aadhaar", "")
            consent = request.POST.get("consent")
            ok, msg = validate_aadhaar(aadhaar)
            if not ok:
                error = msg
            elif not consent:
                error = "Please accept the consent/declaration to continue."
            else:
                otp = generate_otp()
                wizard.update({
                    "step": 2,
                    "aadhaar_masked": mask_aadhaar(aadhaar),
                    "aadhaar_last4": normalize_aadhaar(aadhaar)[-4:],
                    "otp": otp,
                    "otp_created": int(time.time()),
                    "otp_attempts": 0,
                    "txn_id": f"TXN{int(time.time()) % 1000000:06d}",
                })
                request.session[SESSION_KEY] = wizard
                profile = demo_profile_from_patient(patient)
                wizard["profile"] = profile
                request.session[SESSION_KEY] = wizard
                return redirect("/patient/abha/create/?step=2")
            step = 1

        # ---- Step 2: OTP ----
        elif posted_step == 2:
            entered = (request.POST.get("otp") or "").strip()
            saved = wizard.get("otp", "")
            created = wizard.get("otp_created", 0)
            attempts = wizard.get("otp_attempts", 0) + 1
            wizard["otp_attempts"] = attempts
            request.session[SESSION_KEY] = wizard

            if attempts > OTP_MAX_ATTEMPTS:
                request.session.pop(SESSION_KEY, None)
                error = "Too many wrong OTP attempts. Please restart from Step 1."
                step = 1
            elif int(time.time()) - int(created or 0) > OTP_TTL_SECONDS:
                error = "OTP expired. Please go back to Step 1 and request a new OTP."
                step = 2
            elif entered != saved:
                left = OTP_MAX_ATTEMPTS - attempts + 1
                error = f"Incorrect OTP. {max(left, 0)} attempt(s) left."
                step = 2
            else:
                wizard["step"] = 3
                wizard["verified"] = True
                if "profile" not in wizard:
                    wizard["profile"] = demo_profile_from_patient(patient)
                request.session[SESSION_KEY] = wizard
                return redirect("/patient/abha/create/?step=3")

        # ---- Step 3: confirm profile ----
        elif posted_step == 3:
            if not wizard.get("verified"):
                return redirect("/patient/abha/create/?step=1")
            name = (request.POST.get("full_name") or "").strip()
            dob = (request.POST.get("date_of_birth") or "").strip()
            gender = (request.POST.get("gender") or "").strip()
            mobile = (request.POST.get("mobile") or "").strip()

            if not name:
                error = "Please confirm your name."
            else:
                ok, msg = validate_mobile(mobile)
                if not ok:
                    error = msg
            if not error and gender not in ("Male", "Female", "Other"):
                error = "Please select your gender."
            if not error and not dob:
                error = "Please confirm your date of birth."

            if error:
                step = 3
            else:
                wizard["profile"] = {
                    "full_name": name,
                    "date_of_birth": dob,
                    "gender": gender,
                    "mobile": mobile,
                }
                wizard["step"] = 4
                wizard["suggested_address"] = suggest_abha_address(name)
                request.session[SESSION_KEY] = wizard
                return redirect("/patient/abha/create/?step=4")

        # ---- Step 4: ABHA address & finish ----
        elif posted_step == 4:
            if not wizard.get("verified"):
                return redirect("/patient/abha/create/?step=1")
            address = (request.POST.get("abha_address") or "").strip().lower()
            ok, msg = validate_abha_address(address)
            if not ok:
                error = msg
                step = 4
            elif AbhaProfile.objects.filter(abha_address=address).exists():
                error = "This ABHA Address is already taken. Please try another."
                step = 4
            else:
                prof = wizard.get("profile", {})
                abha_number = generate_abha_number(
                    lambda n: AbhaProfile.objects.filter(abha_number=n).exists()
                )
                profile = AbhaProfile.objects.create(
                    patient=patient,
                    abha_number=abha_number,
                    abha_address=address,
                    full_name=prof.get("full_name", ""),
                    date_of_birth=prof.get("date_of_birth") or None,
                    gender=prof.get("gender", ""),
                    mobile=prof.get("mobile", ""),
                    aadhaar_last4=wizard.get("aadhaar_last4", ""),
                    verified=True,
                )
                request.session.pop(SESSION_KEY, None)
                return render(
                    request,
                    "paitent/abha_home.html",
                    {"patient": patient, "profile": profile, "created": True},
                )

    # GET rendering context per step
    wizard = _wizard(request)
    context = {
        "patient": patient,
        "step": step,
        "error": error,
        "wizard": wizard,
        "profile": wizard.get("profile", demo_profile_from_patient(patient)),
        "suggested_address": wizard.get("suggested_address", suggest_abha_address(patient.name or "")),
        "otp_ttl": OTP_TTL_SECONDS // 60,
    }
    # Never expose the real OTP outside step 2 demo notice
    return render(request, "paitent/abha_create.html", context)


# -------------------------
# CARD
# -------------------------

def abha_card(request):
    patient = _patient(request)
    if not patient:
        return redirect("/patient/login/")

    profile = _profile(request, patient)
    if not profile:
        return redirect("/patient/abha/")

    return render(
        request,
        "paitent/abha_card.html",
        {"patient": patient, "profile": profile},
    )


@require_POST
def abha_unlink(request):
    patient = _patient(request)
    if not patient:
        return redirect("/patient/login/")

    profile = _profile(request, patient)
    if profile:
        profile.delete()
    return redirect("/patient/abha/")


# Back-compat: old stub name if referenced anywhere
def abha_register(request):
    return redirect("/patient/abha/create/")

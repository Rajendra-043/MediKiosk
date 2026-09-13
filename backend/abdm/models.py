from django.db import models

from patients.models import Patient


class AbhaProfile(models.Model):
    """ABHA Health ID linked to a patient (demo-mode storage).

    Only masked identity data is kept: last 4 digits of Aadhaar,
    masked mobile for display. Passwords are hashed like elsewhere.
    """

    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="abha_profile",
    )

    # 14-digit ABHA number, stored without spaces/dashes
    abha_number = models.CharField(
        max_length=14,
        unique=True,
    )

    # e.g. rajendra@abdm
    abha_address = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
    )

    full_name = models.CharField(
        max_length=150,
        blank=True,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=20,
        blank=True,
    )

    mobile = models.CharField(
        max_length=15,
        blank=True,
    )

    # Last 4 digits of Aadhaar only - full number is NEVER stored
    aadhaar_last4 = models.CharField(
        max_length=4,
        blank=True,
    )

    # Hashed ABHA password (for linked existing accounts)
    password_hash = models.CharField(
        max_length=128,
        blank=True,
    )

    verified = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def masked_mobile(self):
        if not self.mobile or len(self.mobile) < 4:
            return "XXXXXX XXXX" if not self.mobile else self.mobile
        return f"XXXXXX {self.mobile[-4:]}"

    def formatted_number(self):
        n = self.abha_number or ""
        if len(n) == 14:
            return f"{n[0:4]}-{n[4:8]}-{n[8:12]}-{n[12:14]}"
        return n

    def __str__(self):
        return f"{self.patient_id} - {self.abha_number}"

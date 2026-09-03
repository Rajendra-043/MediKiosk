from django.db import models

# Create your models here.


class Doctor(models.Model):
    doctor_id = models.CharField(
        max_length=20,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    medical_registration_number = models.CharField(
        max_length=100,
        unique=True
    )

    specialization = models.CharField(
        max_length=100
    )

    qualification = models.CharField(
        max_length=200
    )

    experience = models.PositiveIntegerField()

    phone = models.CharField(
        max_length=15
    )

    email = models.EmailField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.doctor_id
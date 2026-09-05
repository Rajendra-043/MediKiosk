from django.db import models


class Patient(models.Model):
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        null=True ,
        blank= True
    )

    name = models.CharField(
        max_length=100
    )

    date_of_birth = models.DateField( null=True,blank=True)


    gender = models.CharField(
        max_length=20
    )

    blood_group = models.CharField(
        max_length=5,
        blank=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )
    passward = models.CharField(max_length=128,null= True,blank = True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.patient_id

class MedicalHistory(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="medical_history"
    )

    condition = models.CharField(
        max_length=200
    )

    diagnosis = models.TextField(
        blank=True
    )

    diagnosed_date = models.DateField(
        null=True,
        blank=True
    )

    doctor_name = models.CharField(
        max_length=150,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.patient.patient_id} - {self.condition}"
    

class Medication(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="medications"
    )

    name = models.CharField(
        max_length=200
    )

    generic_name = models.CharField(
        max_length=200,
        blank=True
    )

    dosage = models.CharField(
        max_length=100,
        blank=True
    )

    frequency = models.CharField(
        max_length=100,
        blank=True
    )

    route = models.CharField(
        max_length=100,
        default="Oral",
        blank=True
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    end_date = models.DateField(
        null=True,
        blank=True
    )

    instructions = models.TextField(
        blank=True
    )

    doctor = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.patient.patient_id} - {self.name}"



class MedicalDocument(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    document_name = models.CharField(
        max_length=200
    )

    document_type = models.CharField(
        max_length=100,
        blank=True
    )

    file = models.FileField(
        upload_to="medical_documents/"
    )

    description = models.TextField(
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.patient.patient_id} - {self.document_name}"
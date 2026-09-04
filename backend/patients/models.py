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
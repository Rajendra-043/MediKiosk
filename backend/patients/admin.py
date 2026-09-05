from django.contrib import admin
from .models import Patient, MedicalHistory, Medication, MedicalDocument

admin.site.register(Patient)
admin.site.register(MedicalHistory)
admin.site.register(Medication)
admin.site.register(MedicalDocument)
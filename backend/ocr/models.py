from django.db import models


class OCRDocument(models.Model):

    document_name = models.CharField(
        max_length=255
    )

    file = models.FileField(
        upload_to="medical_documents/"
    )

    extracted_text = models.TextField(
        blank=True
    )

    report = models.TextField(
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.document_name
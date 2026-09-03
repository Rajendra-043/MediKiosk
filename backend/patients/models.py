from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20)
    phone = models.CharField(max_length=15, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



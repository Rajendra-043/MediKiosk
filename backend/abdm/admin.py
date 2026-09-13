from django.contrib import admin

from .models import AbhaProfile


@admin.register(AbhaProfile)
class AbhaProfileAdmin(admin.ModelAdmin):
    list_display = ("abha_number", "abha_address", "full_name", "verified", "created_at")
    search_fields = ("abha_number", "abha_address", "full_name")
    list_filter = ("verified",)

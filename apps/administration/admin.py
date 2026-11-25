"""Administration admin."""
from django.contrib import admin
from .models import ApiToken, OrganizationSettings, DataExport


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "organization", "is_active", "last_used_at")


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "default_currency", "enable_email", "enable_whatsapp")


@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "export_type", "status", "created_at")

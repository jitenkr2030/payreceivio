"""Customer portal admin."""
from django.contrib import admin
from .models import PortalUser, PortalRequest


@admin.register(PortalUser)
class PortalUserAdmin(admin.ModelAdmin):
    list_display = ("email", "customer", "is_active", "last_login_at")


@admin.register(PortalRequest)
class PortalRequestAdmin(admin.ModelAdmin):
    list_display = ("customer", "request_type", "subject", "status", "created_at")
    list_filter = ("status", "request_type")

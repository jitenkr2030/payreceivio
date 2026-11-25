"""Admin for audit."""
from django.contrib import admin

from .models import AuditLog, DataAccessLog, ApprovalRequest


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "organization", "action", "entity_type", "entity_id")
    list_filter = ("action", "entity_type", "organization")
    search_fields = ("entity_type", "entity_id", "entity_label", "user__email")
    readonly_fields = [f.name for f in AuditLog._meta.fields]


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "organization", "data_type", "access_reason")
    list_filter = ("data_type", "organization")


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("created_at", "organization", "requested_by", "request_type", "status", "reviewed_by")
    list_filter = ("status", "organization")

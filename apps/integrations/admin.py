"""Integrations admin."""
from django.contrib import admin
from .models import Connector, AccountingConnection, SyncJob, SyncLog, SyncError


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "vendor", "auth_method", "is_active")


@admin.register(AccountingConnection)
class AccountingConnectionAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "connector", "status", "last_sync_at", "is_active")
    list_filter = ("status", "is_active", "connector")


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ("connection", "direction", "status", "started_at", "completed_at", "records_processed")
    list_filter = ("status", "direction")


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("job", "level", "entity_type", "message", "created_at")
    list_filter = ("level",)


@admin.register(SyncError)
class SyncErrorAdmin(admin.ModelAdmin):
    list_display = ("job", "entity_type", "entity_id", "retry_count", "is_resolved")

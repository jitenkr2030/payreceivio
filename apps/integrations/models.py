"""
Integrations framework models.

Provides a unified interface for all accounting connectors:
- AccountingConnection: per-company connection to an accounting platform
- Connector: registry of available connectors
- SyncJob: a synchronization run
- SyncLog: individual log entry within a SyncJob
- SyncError: failed records for retry
"""
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel, TimeStampedModel


class Connector(TimeStampedModel):
    """Registry of available accounting connectors."""

    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    vendor = models.CharField(max_length=100)
    auth_method = models.CharField(max_length=50, choices=[
        ("api_key", "API Key"),
        ("oauth2", "OAuth 2.0"),
        ("basic", "Basic Auth"),
        ("local_agent", "Local Agent"),
        ("file", "File-based"),
    ])
    supported_entities = models.JSONField(default=list, help_text="List of entities this connector supports")
    is_active = models.BooleanField(default=True)
    config_schema = models.JSONField(default=dict, help_text="JSON schema for connection config")
    documentation_url = models.URLField(blank=True)


class AccountingConnection(TenantOwnedModel):
    """A connection between a PayReceivio company and an accounting platform."""

    STATUS = [
        ("active", "Active"),
        ("disconnected", "Disconnected"),
        ("error", "Error"),
        ("expired", "Expired"),
        ("pending", "Pending Setup"),
    ]

    company = models.ForeignKey("organizations.Company", on_delete=models.CASCADE, related_name="accounting_connections")
    connector = models.ForeignKey(Connector, on_delete=models.PROTECT, related_name="connections")
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS, default="pending", db_index=True)
    # Auth credentials (encrypted at rest in production via field-level encryption)
    credentials = models.JSONField(default=dict, blank=True, help_text="OAuth tokens, API keys, etc.")
    config = models.JSONField(default=dict, blank=True, help_text="Connector-specific configuration")
    # Sync settings
    sync_frequency = models.CharField(max_length=20, default="hourly", choices=[
        ("manual", "Manual"),
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
    ])
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, blank=True)
    last_sync_records = models.PositiveIntegerField(default=0)
    next_sync_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Webhook config
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Accounting connection"
        verbose_name_plural = "Accounting connections"
        unique_together = (("organization", "company", "connector", "name"),)
        indexes = [models.Index(fields=["organization", "status", "is_active"])]


class SyncJob(TimeStampedModel):
    STATUS = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    DIRECTION = [
        ("import", "Import (Accounting → PayReceivio)"),
        ("export", "Export (PayReceivio → Accounting)"),
        ("bidirectional", "Bidirectional"),
    ]

    connection = models.ForeignKey(AccountingConnection, on_delete=models.CASCADE, related_name="sync_jobs")
    direction = models.CharField(max_length=20, choices=DIRECTION, default="import")
    status = models.CharField(max_length=20, choices=STATUS, default="queued", db_index=True)
    entity_type = models.CharField(max_length=50, blank=True, help_text="Specific entity or empty for full sync")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    is_manual = models.BooleanField(default=False)


class SyncLog(TimeStampedModel):
    LEVEL = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("debug", "Debug"),
    ]
    job = models.ForeignKey(SyncJob, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=20, choices=LEVEL, default="info")
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)


class SyncError(TimeStampedModel):
    """Failed sync record for retry queue."""
    job = models.ForeignKey(SyncJob, on_delete=models.CASCADE, related_name="errors")
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=100)
    error_message = models.TextField()
    payload = models.JSONField(default=dict)
    retry_count = models.PositiveIntegerField(default=0)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

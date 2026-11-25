"""Administration models."""
import uuid
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class ApiToken(TenantOwnedModel):
    name = models.CharField(max_length=200)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_tokens")
    scopes = models.JSONField(default=list, blank=True, help_text="List of permitted scopes")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)


class OrganizationSettings(TenantOwnedModel):
    """Organization-wide settings singleton per org."""
    organization = models.OneToOneField("organizations.Organization", on_delete=models.CASCADE, related_name="settings_obj")
    default_currency = models.CharField(max_length=10, default="INR")
    default_payment_terms = models.CharField(max_length=100, default="30 days")
    reminder_schedule = models.JSONField(default=dict, blank=True)
    dunning_threshold_days = models.PositiveIntegerField(default=30)
    auto_post_receipts = models.BooleanField(default=False)
    require_approval_for_receipt_posting = models.BooleanField(default=True)
    allow_customer_portal = models.BooleanField(default=True)
    customer_portal_url = models.URLField(blank=True)
    enable_whatsapp = models.BooleanField(default=False)
    enable_sms = models.BooleanField(default=False)
    enable_email = models.BooleanField(default=True)
    email_from_address = models.EmailField(blank=True)
    whatsapp_from_number = models.CharField(max_length=20, blank=True)
    sms_sender_id = models.CharField(max_length=20, blank=True)


class DataExport(TenantOwnedModel):
    """Tracks data export requests for audit."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="data_exports")
    export_type = models.CharField(max_length=100)
    filters = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to="exports/", null=True, blank=True)
    status = models.CharField(max_length=20, default="pending", choices=[
        ("pending", "Pending"), ("processing", "Processing"),
        ("completed", "Completed"), ("failed", "Failed"),
    ])
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

"""Customer portal models."""
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class PortalUser(TenantOwnedModel):
    """Customer-side login (separate from internal users)."""
    customer = models.OneToOneField("customers.Customer", on_delete=models.CASCADE, related_name="portal_user")
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    password_hash = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    otp_secret = models.CharField(max_length=100, blank=True)
    notification_prefs = models.JSONField(default=dict, blank=True)


class PortalRequest(TenantOwnedModel):
    """A request raised by a customer through the portal."""
    REQUEST_TYPES = [
        ("payment_dispute", "Payment Dispute"),
        ("invoice_corrections", "Invoice Correction"),
        ("contact_update", "Contact Update Request"),
        ("statement_request", "Statement Request"),
        ("payment_plan", "Payment Plan Request"),
        ("support", "General Support"),
    ]
    STATUS = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    ]
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="portal_requests")
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES, default="support")
    subject = models.CharField(max_length=300)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default="open", db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    resolved_at = models.DateTimeField(null=True, blank=True)

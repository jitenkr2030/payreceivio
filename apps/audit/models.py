"""
Audit models: AuditLog, ApprovalRequest, DataAccessLog.

AuditLog captures every financial operation (create/update/delete on
key models). ApprovalRequest is used for workflows that need sign-off
(receipt posting, credit limit changes, etc.).
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """Generic audit log entry."""

    ACTIONS = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("view", "View"),
        ("approve", "Approve"),
        ("reject", "Reject"),
        ("post", "Post"),
        ("sync", "Sync"),
        ("login", "Login"),
        ("logout", "Logout"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, related_name="+")
    action = models.CharField(max_length=20, choices=ACTIONS, db_index=True)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=50, db_index=True)
    entity_label = models.CharField(max_length=300, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Audit log")
        verbose_name_plural = _("Audit logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "entity_type", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.created_at} {self.user} {self.action} {self.entity_type}:{self.entity_id}"


class DataAccessLog(models.Model):
    """Tracks sensitive data access (export, customer PII view, etc.)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True)
    data_type = models.CharField(max_length=100, db_index=True)
    record_ids = models.JSONField(default=list, blank=True)
    access_reason = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "data_type", "-created_at"])]


class ApprovalRequest(models.Model):
    """Approval workflow for financial operations."""

    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="approvals")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approval_requests")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=50, db_index=True)
    request_type = models.CharField(max_length=100)
    description = models.TextField()
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS, default="pending", db_index=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "status", "-created_at"])]

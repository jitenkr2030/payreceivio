"""Notifications models."""
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class Notification(TenantOwnedModel):
    NOTIF_TYPES = [
        ("invoice_synced", "Invoice Synchronised"),
        ("invoice_due_approach", "Invoice Approaching Due Date"),
        ("invoice_overdue", "Invoice Overdue"),
        ("payment_received", "Payment Received"),
        ("payment_failed", "Payment Failed"),
        ("payment_unallocated", "Payment Partially Allocated"),
        ("unmatched_bank_txn", "Unmatched Bank Transaction"),
        ("credit_limit_exceeded", "Credit Limit Exceeded"),
        ("commitment_missed", "Collection Commitment Missed"),
        ("task_assigned", "Collection Task Assigned"),
        ("task_overdue", "Collection Task Overdue"),
        ("recon_pending_approval", "Reconciliation Pending Approval"),
        ("receipt_sync_failed", "Receipt Sync Failed"),
        ("integration_disconnected", "Integration Disconnected"),
        ("sync_failed", "Sync Failed"),
        ("subscription_renewal", "Subscription Renewal Approaching"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=50, choices=NOTIF_TYPES, db_index=True)
    title = models.CharField(max_length=300)
    message = models.TextField()
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.CharField(max_length=50, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "-created_at"])]

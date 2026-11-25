"""
Collection models - tasks, follow-ups, promise-to-pay, visits.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantOwnedModel, TimeStampedModel


class CollectionTask(TenantOwnedModel):
    """A follow-up task assigned to a collection executive."""

    PRIORITY = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    STATUS = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("overdue", "Overdue"),
    ]
    TYPE = [
        ("call", "Call"),
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
        ("visit", "Visit"),
        ("reminder", "Reminder"),
        ("escalation", "Escalation"),
        ("statement_share", "Statement Share"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="collection_tasks")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="collection_tasks")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="collection_tasks")
    task_type = models.CharField(max_length=30, choices=TYPE, default="call")
    priority = models.CharField(max_length=20, choices=PRIORITY, default="medium")
    status = models.CharField(max_length=20, choices=STATUS, default="open", db_index=True)
    due_date = models.DateField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    escalation_level = models.PositiveIntegerField(default=0)
    parent_task = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subtasks")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Collection task")
        verbose_name_plural = _("Collection tasks")
        ordering = ["-due_date", "-id"]
        indexes = [
            models.Index(fields=["organization", "assigned_to", "status"]),
            models.Index(fields=["organization", "customer", "status"]),
            models.Index(fields=["organization", "due_date"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.customer.name} ({self.get_status_display()})"


class FollowUp(TenantOwnedModel):
    """A follow-up interaction log entry."""

    CHANNEL = [
        ("call", "Call"),
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
        ("sms", "SMS"),
        ("visit", "Visit"),
        ("other", "Other"),
    ]
    OUTCOME = [
        ("no_response", "No Response"),
        ("promise_to_pay", "Promise to Pay"),
        ("paid", "Paid"),
        ("dispute", "Dispute Raised"),
        ("callback_requested", "Callback Requested"),
        ("customer_unreachable", "Customer Unreachable"),
        ("other", "Other"),
    ]

    task = models.ForeignKey(CollectionTask, on_delete=models.CASCADE, null=True, blank=True, related_name="followups")
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="followups")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="followups")
    channel = models.CharField(max_length=20, choices=CHANNEL, default="call")
    outcome = models.CharField(max_length=30, choices=OUTCOME, default="no_response")
    contact_person = models.CharField(max_length=200, blank=True)
    notes = models.TextField()
    followup_at = models.DateTimeField(auto_now_add=True)
    followed_up_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="followups")
    next_action_date = models.DateField(null=True, blank=True)
    next_action = models.CharField(max_length=200, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Follow-up")
        verbose_name_plural = _("Follow-ups")
        ordering = ["-followup_at"]
        indexes = [models.Index(fields=["organization", "customer", "-followup_at"])]


class PromiseToPay(TenantOwnedModel):
    """Customer's commitment to pay by a certain date."""

    STATUS = [
        ("pending", "Pending"),
        ("fulfilled", "Fulfilled"),
        ("broken", "Broken"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="promises")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="promises")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    promised_date = models.DateField(db_index=True)
    actual_payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="recorded_promises")
    source = models.CharField(max_length=20, default="call", choices=[
        ("call", "Phone Call"), ("email", "Email"), ("portal", "Customer Portal"),
        ("visit", "Field Visit"), ("whatsapp", "WhatsApp"), ("other", "Other")
    ])

    class Meta:
        verbose_name = _("Promise to pay")
        verbose_name_plural = _("Promises to pay")
        ordering = ["-promised_date"]
        indexes = [models.Index(fields=["organization", "status", "-promised_date"])]


class CollectionVisit(TenantOwnedModel):
    """Field collection visit log."""

    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="visits")
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="visits")
    planned_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    check_in_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    check_in_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    check_out_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    check_out_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    visit_purpose = models.CharField(max_length=200, blank=True)
    outcome = models.TextField(blank=True)
    amount_collected = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="planned", choices=[
        ("planned", "Planned"), ("checked_in", "Checked In"),
        ("completed", "Completed"), ("cancelled", "Cancelled")
    ])

    class Meta:
        verbose_name = _("Collection visit")
        verbose_name_plural = _("Collection visits")
        ordering = ["-planned_at", "-id"]


class CollectionNote(TenantOwnedModel):
    """Internal note about a customer's collection situation."""

    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="collection_notes")
    note = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="collection_notes")

    class Meta:
        verbose_name = _("Collection note")
        verbose_name_plural = _("Collection notes")
        ordering = ["-created_at"]

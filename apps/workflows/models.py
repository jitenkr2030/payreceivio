"""Workflow models - workflow, rule, execution."""
from django.conf import settings
from django.db import models

from apps.common.models import TenantOwnedModel, TimeStampedModel


class Workflow(TenantOwnedModel):
    """A named workflow containing ordered steps."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_event = models.CharField(max_length=50, db_index=True, choices=[
        ("invoice_overdue", "Invoice Overdue"),
        ("invoice_due_today", "Invoice Due Today"),
        ("invoice_due_soon", "Invoice Due Soon"),
        ("payment_received", "Payment Received"),
        ("payment_failed", "Payment Failed"),
        ("credit_limit_breach", "Credit Limit Breach"),
        ("customer_risk_change", "Customer Risk Changed"),
        ("promise_broken", "Promise to Pay Broken"),
        ("manual", "Manual Trigger"),
    ])
    trigger_conditions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=10)
    last_run_at = models.DateTimeField(null=True, blank=True)
    total_executions = models.PositiveIntegerField(default=0)
    successful_executions = models.PositiveIntegerField(default=0)
    failed_executions = models.PositiveIntegerField(default=0)


class WorkflowStep(TimeStampedModel):
    """An ordered step within a workflow."""

    ACTION_TYPES = [
        ("send_message", "Send Message"),
        ("create_task", "Create Collection Task"),
        ("assign_salesperson", "Assign Salesperson"),
        ("escalate", "Escalate"),
        ("wait", "Wait"),
        ("update_status", "Update Status"),
        ("create_promise", "Create Promise to Pay"),
        ("generate_receipt", "Generate Receipt"),
        ("sync_accounting", "Sync to Accounting"),
        ("webhook", "Call Webhook"),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveIntegerField(default=0)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    config = models.JSONField(default=dict, help_text="Step configuration parameters")
    condition = models.CharField(max_length=300, blank=True, help_text="Optional condition expression")


class WorkflowExecution(TimeStampedModel):
    """An execution instance of a workflow."""

    STATUS = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="executions")
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    trigger_event = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS, default="running")
    current_step = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    log = models.JSONField(default=list, blank=True)

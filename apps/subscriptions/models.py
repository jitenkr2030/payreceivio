"""Subscriptions models - plans, subscriptions, usage, billing."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.common.models import TimeStampedModel


class Plan(TimeStampedModel):
    """SaaS subscription plan."""

    name = models.CharField(max_length=100, db_index=True)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    currency = models.CharField(max_length=10, default="INR")
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)
    trial_days = models.PositiveIntegerField(default=14)
    # Limits
    max_companies = models.PositiveIntegerField(default=1)
    max_branches = models.PositiveIntegerField(default=1)
    max_users = models.PositiveIntegerField(default=5)
    max_invoices_per_month = models.PositiveIntegerField(default=100)
    max_messages_per_month = models.PositiveIntegerField(default=100)
    max_accounting_connections = models.PositiveIntegerField(default=1)
    # Feature flags
    features = models.JSONField(default=dict, help_text="Feature flags for this plan")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"
        ordering = ["sort_order", "monthly_price"]


class Subscription(TimeStampedModel):
    """An organization's subscription."""

    STATUS = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
    ]
    BILLING_CYCLE = [
        ("monthly", "Monthly"),
        ("annual", "Annual"),
    ]

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=STATUS, default="trial", db_index=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE, default="monthly")
    started_at = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)
    # Payment
    gateway_subscription_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    auto_renew = models.BooleanField(default=True)
    # Discount
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ["-started_at"]


class UsageRecord(TimeStampedModel):
    """Monthly usage tracking per organization."""
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="usage_records")
    period_start = models.DateField()
    period_end = models.DateField()
    invoice_count = models.PositiveIntegerField(default=0)
    message_count = models.PositiveIntegerField(default=0)
    user_count = models.PositiveIntegerField(default=0)
    company_count = models.PositiveIntegerField(default=0)
    branch_count = models.PositiveIntegerField(default=0)
    payment_count = models.PositiveIntegerField(default=0)
    storage_used_mb = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))


class BillingInvoice(TimeStampedModel):
    """Invoice raised by PayReceivio to a customer organization."""
    STATUS = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="billing_invoices")
    invoice_number = models.CharField(max_length=100, db_index=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    paid_at = models.DateTimeField(null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    pdf_file = models.FileField(upload_to="billing-invoices/", null=True, blank=True)


class PlanDefaults:
    """Helper to seed default plans."""
    DEFAULTS = [
        {"name": "trial", "label": "Free Trial", "monthly_price": 0, "annual_price": 0,
         "max_companies": 1, "max_branches": 1, "max_users": 2, "max_invoices_per_month": 50,
         "max_messages_per_month": 50, "max_accounting_connections": 1, "is_trial": True, "trial_days": 14},
        {"name": "starter", "label": "Starter", "monthly_price": 999, "annual_price": 9990,
         "max_companies": 1, "max_branches": 1, "max_users": 5, "max_invoices_per_month": 500,
         "max_messages_per_month": 500, "max_accounting_connections": 1},
        {"name": "growth", "label": "Growth", "monthly_price": 1999, "annual_price": 19990,
         "max_companies": 1, "max_branches": 3, "max_users": 15, "max_invoices_per_month": 5000,
         "max_messages_per_month": 5000, "max_accounting_connections": 2},
        {"name": "professional", "label": "Professional", "monthly_price": 4999, "annual_price": 49990,
         "max_companies": 3, "max_branches": 10, "max_users": 50, "max_invoices_per_month": 50000,
         "max_messages_per_month": 50000, "max_accounting_connections": 5},
        {"name": "business", "label": "Business", "monthly_price": 9999, "annual_price": 99990,
         "max_companies": 10, "max_branches": 50, "max_users": 200, "max_invoices_per_month": 500000,
         "max_messages_per_month": 500000, "max_accounting_connections": 10},
        {"name": "enterprise", "label": "Enterprise", "monthly_price": 0, "annual_price": 0,
         "max_companies": 999, "max_branches": 999, "max_users": 999, "max_invoices_per_month": 999999,
         "max_messages_per_month": 999999, "max_accounting_connections": 999,
         "description": "Custom pricing. Contact sales."},
    ]

"""Targets models."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class CollectionTarget(TenantOwnedModel):
    PERIOD = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annual", "Annual"),
    ]
    SCOPE = [
        ("organization", "Organization"),
        ("company", "Company"),
        ("branch", "Branch"),
        ("department", "Department"),
        ("salesperson", "Salesperson"),
        ("customer", "Customer"),
    ]

    name = models.CharField(max_length=200)
    period = models.CharField(max_length=20, choices=PERIOD, db_index=True)
    scope = models.CharField(max_length=20, choices=SCOPE, default="organization")
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    achieved_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    start_date = models.DateField()
    end_date = models.DateField()
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="targets")
    customer = models.ForeignKey("customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="targets")
    is_active = models.BooleanField(default=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        verbose_name = "Collection target"
        verbose_name_plural = "Collection targets"
        ordering = ["-start_date"]


class CollectionMetric(TenantOwnedModel):
    """Daily collection metric snapshot for analytics."""
    metric_date = models.DateField(db_index=True)
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="metrics")
    customer = models.ForeignKey("customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="metrics")
    total_collected = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    invoice_count = models.PositiveIntegerField(default=0)
    overdue_count = models.PositiveIntegerField(default=0)
    promises_pending = models.PositiveIntegerField(default=0)
    tasks_open = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)

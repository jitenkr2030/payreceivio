"""Disputes models."""
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class Dispute(TenantOwnedModel):
    DISPUTE_TYPES = [
        ("short_payment", "Short Payment"),
        ("excess_payment", "Excess Payment"),
        ("damaged_goods", "Damaged Goods"),
        ("price_difference", "Price Difference"),
        ("tax_discrepancy", "Tax Discrepancy"),
        ("duplicate_invoice", "Duplicate Invoice"),
        ("sales_return", "Sales Return"),
        ("other", "Other"),
    ]
    STATUS = [
        ("open", "Open"),
        ("under_review", "Under Review"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    dispute_number = models.CharField(max_length=100, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="disputes")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="disputes")
    dispute_type = models.CharField(max_length=30, choices=DISPUTE_TYPES, default="other")
    amount_in_dispute = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default="open", db_index=True)
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_disputes")
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        verbose_name = "Dispute"
        verbose_name_plural = "Disputes"
        unique_together = (("organization", "dispute_number"),)
        ordering = ["-created_at"]


class DisputeComment(models.Model):
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField()
    commented_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

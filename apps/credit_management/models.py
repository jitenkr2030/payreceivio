"""Credit management models."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel, TimeStampedModel


class CreditLimit(TenantOwnedModel):
    customer = models.OneToOneField("customers.Customer", on_delete=models.CASCADE, related_name="credit_limit_record")
    limit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    period_days = models.PositiveIntegerField(default=30)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    approved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)


class CreditAssessment(TimeStampedModel):
    """A snapshot of a customer's credit risk at a point in time."""
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="credit_assessments")
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="credit_assessments")
    assessment_date = models.DateField(db_index=True)
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    overdue_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    average_payment_delay_days = models.PositiveIntegerField(default=0)
    payment_reliability_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"),
                                                     help_text="0-100, higher is better")
    risk_category = models.CharField(max_length=20, default="medium",
                                     choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("blocked", "Blocked")])
    recommended_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)
    assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    factors = models.JSONField(default=dict, help_text="Scoring factors and weights")


class CreditAlert(TenantOwnedModel):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="credit_alerts")
    alert_type = models.CharField(max_length=50, choices=[
        ("limit_breach", "Credit Limit Breach"),
        ("period_breach", "Credit Period Breach"),
        ("high_overdue", "High Overdue Amount"),
        ("payment_delay", "Payment Delay Increasing"),
        ("risk_change", "Risk Category Changed"),
    ])
    severity = models.CharField(max_length=20, default="medium",
                                choices=[("info", "Info"), ("warning", "Warning"), ("critical", "Critical")])
    message = models.TextField()
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    acknowledged_at = models.DateTimeField(null=True, blank=True)

"""Credit admin."""
from django.contrib import admin
from .models import CreditLimit, CreditAssessment, CreditAlert


@admin.register(CreditLimit)
class CreditLimitAdmin(admin.ModelAdmin):
    list_display = ("customer", "limit_amount", "period_days", "is_active")


@admin.register(CreditAssessment)
class CreditAssessmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "assessment_date", "outstanding_amount", "overdue_amount",
                    "payment_reliability_score", "risk_category")


@admin.register(CreditAlert)
class CreditAlertAdmin(admin.ModelAdmin):
    list_display = ("customer", "alert_type", "severity", "is_acknowledged", "created_at")

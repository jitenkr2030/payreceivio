"""Targets admin."""
from django.contrib import admin
from .models import CollectionTarget, CollectionMetric


@admin.register(CollectionTarget)
class CollectionTargetAdmin(admin.ModelAdmin):
    list_display = ("name", "period", "scope", "target_amount", "achieved_amount", "start_date", "end_date")


@admin.register(CollectionMetric)
class CollectionMetricAdmin(admin.ModelAdmin):
    list_display = ("metric_date", "salesperson", "total_collected", "invoice_count", "overdue_count")

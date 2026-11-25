"""Disputes admin."""
from django.contrib import admin
from .models import Dispute, DisputeComment


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ("dispute_number", "customer", "dispute_type", "amount_in_dispute", "status", "created_at")
    list_filter = ("status", "dispute_type")


@admin.register(DisputeComment)
class DisputeCommentAdmin(admin.ModelAdmin):
    list_display = ("dispute", "commented_by", "created_at")

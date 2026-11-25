"""Payment admin."""
from django.contrib import admin

from .models import Payment, PaymentLink, PaymentTransaction, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_number", "customer", "payment_date", "amount",
                    "allocated_amount", "payment_method", "status", "is_reconciled", "organization")
    list_filter = ("status", "payment_method", "is_reconciled", "organization")
    search_fields = ("payment_number", "customer__name", "reference", "gateway_transaction_id")
    autocomplete_fields = ("organization", "customer", "received_by")


@admin.register(PaymentLink)
class PaymentLinkAdmin(admin.ModelAdmin):
    list_display = ("link_id", "customer", "amount", "status", "created_at")
    list_filter = ("status", "organization")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("gateway", "gateway_transaction_id", "amount", "status", "processed_at")
    list_filter = ("gateway", "status")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("refund_number", "payment", "amount", "status", "refund_date")
    list_filter = ("status",)

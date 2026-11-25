"""Receivables admin."""
from django.contrib import admin

from .models import Invoice, InvoiceLine, CreditNote, DebitNote, InvoiceAllocation


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "invoice_date", "due_date", "total_amount",
                    "paid_amount", "outstanding_amount", "status", "organization")
    list_filter = ("status", "organization", "invoice_date")
    search_fields = ("invoice_number", "customer__name", "accounting_ref")
    autocomplete_fields = ("organization", "customer", "salesperson")
    inlines = [InvoiceLineInline]
    date_hierarchy = "invoice_date"


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ("credit_note_number", "customer", "invoice", "date", "amount", "adjusted_amount", "is_adjusted")
    list_filter = ("is_adjusted", "organization")


@admin.register(DebitNote)
class DebitNoteAdmin(admin.ModelAdmin):
    list_display = ("debit_note_number", "customer", "invoice", "date", "amount")
    list_filter = ("organization",)


@admin.register(InvoiceAllocation)
class InvoiceAllocationAdmin(admin.ModelAdmin):
    list_display = ("payment", "invoice", "amount", "allocated_by", "allocation_type")
    list_filter = ("allocation_type",)

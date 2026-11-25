"""Customer admin."""
from django.contrib import admin

from .models import Customer, CustomerContact, CustomerLedgerEntry


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "phone", "gst_number", "risk_category", "is_active")
    list_filter = ("is_active", "risk_category", "organization")
    search_fields = ("code", "name", "phone", "email", "gst_number")
    autocomplete_fields = ("organization", "company", "branch", "salesperson", "territory")


@admin.register(CustomerContact)
class CustomerContactAdmin(admin.ModelAdmin):
    list_display = ("name", "customer", "designation", "email", "phone", "is_primary")
    list_filter = ("is_primary", "is_accounts_contact")


@admin.register(CustomerLedgerEntry)
class CustomerLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_date", "customer", "entry_type", "amount", "reference", "organization")
    list_filter = ("entry_type", "organization")
    search_fields = ("customer__name", "reference")
    autocomplete_fields = ("organization", "customer")

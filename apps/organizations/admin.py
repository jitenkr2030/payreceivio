"""Admin for organizations."""
from django.contrib import admin

from .models import Organization, Company, Branch, Department, Territory


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "gst_number", "subscription_plan", "is_active", "created_at")
    list_filter = ("is_active", "subscription_plan", "country")
    search_fields = ("name", "legal_name", "email", "gst_number")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ()


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "gst_number", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("name", "legal_name", "gst_number")
    autocomplete_fields = ("organization",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "is_head_office", "is_active")
    list_filter = ("is_active", "is_head_office", "company__organization")
    search_fields = ("name", "code")
    autocomplete_fields = ("company",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "head", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("name", "code")


@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "parent", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("name", "code")

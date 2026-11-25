"""Admin for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Role, RoleAssignment, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "phone", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "mfa_enabled")
    search_fields = ("email", "full_name", "phone")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("full_name", "phone", "avatar")}),
        ("Verification", {"fields": ("is_email_verified", "is_phone_verified", "mfa_enabled")}),
        ("Preferences", {"fields": ("timezone", "date_format",
                                    "notification_email", "notification_sms", "notification_whatsapp")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Audit", {"fields": ("last_login_ip", "last_active_at", "last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2"),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "organization", "is_system", "is_active")
    list_filter = ("is_system", "is_active")
    search_fields = ("name", "label")
    filter_horizontal = ("permissions",)


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "organization", "company", "branch", "is_active", "assigned_at")
    list_filter = ("is_active", "role", "organization")
    search_fields = ("user__email", "user__full_name")
    autocomplete_fields = ("user", "role", "organization", "company", "branch")


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "activity_type", "ip_address", "created_at")
    list_filter = ("activity_type",)
    search_fields = ("user__email", "ip_address")
    readonly_fields = ("user", "activity_type", "ip_address", "user_agent", "metadata", "created_at")

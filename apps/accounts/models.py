"""
User, Role and Permission models for PayReceivio.

Custom user with email login. RBAC is implemented with Roles linked to Users
per organization; field-level restrictions are handled by RolePermission
records.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Email-based user manager."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user - email login, MFA-ready, org memberships via RoleAssignment."""

    username = None
    email = models.EmailField(_("Email"), unique=True, db_index=True)
    full_name = models.CharField(_("Full name"), max_length=200)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    avatar = models.ImageField(_("Avatar"), upload_to="avatars/", null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_active_at = models.DateTimeField(null=True, blank=True)

    # Preferences
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    date_format = models.CharField(max_length=20, default="DD/MM/YYYY")
    notification_email = models.BooleanField(default=True)
    notification_sms = models.BooleanField(default=False)
    notification_whatsapp = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def display_name(self):
        return self.full_name or self.email

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split(" ")[0] if self.full_name else self.email

    def has_role(self, role_name, organization=None):
        """Check if user has a specific role in an organization."""
        qs = self.role_assignments.filter(role__name=role_name)
        if organization:
            qs = qs.filter(organization=organization)
        return qs.exists()

    def is_org_owner(self, organization):
        return self.role_assignments.filter(
            organization=organization, role__name="org_owner"
        ).exists()

    def get_primary_organization(self):
        """Return the user's primary organization (first or None)."""
        assignment = self.role_assignments.select_related("organization").first()
        return assignment.organization if assignment else None


class Role(models.Model):
    """Role definitions. System roles are seeded; custom roles can be added."""

    SYSTEM_ROLES = [
        ("super_admin", "SaaS Super Admin"),
        ("org_owner", "Organisation Owner"),
        ("business_admin", "Business Administrator"),
        ("finance_manager", "Finance Manager"),
        ("accountant", "Accountant"),
        ("collection_manager", "Collection Manager"),
        ("collection_executive", "Collection Executive"),
        ("sales_manager", "Sales Manager"),
        ("salesperson", "Salesperson"),
        ("auditor", "Auditor"),
        ("customer", "Customer"),
    ]

    name = models.CharField(max_length=50, choices=SYSTEM_ROLES, db_index=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="roles",
        verbose_name=_("Organization"),
    )
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        unique_together = (("name", "organization"),)
        indexes = [
            models.Index(fields=["name", "organization"]),
        ]

    def __str__(self):
        return f"{self.label} ({self.organization})" if self.organization else self.label


class RoleAssignment(models.Model):
    """Assigns a user to a role in an organization (optionally company/branch)."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey("accounts.Role", on_delete=models.PROTECT, related_name="assignments")
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    company = models.ForeignKey(
        "organizations.Company",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="role_assignments",
    )
    branch = models.ForeignKey(
        "organizations.Branch",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="role_assignments",
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_roles",
    )

    class Meta:
        verbose_name = _("Role assignment")
        verbose_name_plural = _("Role assignments")
        unique_together = (("user", "role", "organization"),)
        indexes = [
            models.Index(fields=["user", "organization"]),
            models.Index(fields=["organization", "role"]),
        ]

    def __str__(self):
        scope = f"{self.organization}"
        if self.company:
            scope += f" / {self.company}"
        return f"{self.user} → {self.role.label} @ {scope}"


class UserActivity(models.Model):
    """Tracks user login/logout and other authentication events."""

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=50)  # login, logout, mfa_enable, etc.
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User activity")
        verbose_name_plural = _("User activities")
        indexes = [models.Index(fields=["user", "activity_type", "-created_at"])]

    def __str__(self):
        return f"{self.user} {self.activity_type} @ {self.created_at}"


# Add reverse relation helper to User
def user_organizations(self):
    """Return organizations the user has access to via role assignments."""
    from apps.organizations.models import Organization
    org_ids = self.role_assignments.filter(is_active=True).values_list("organization_id", flat=True).distinct()
    return Organization.objects.filter(pk__in=org_ids)


User.add_to_class("organizations", property(user_organizations))

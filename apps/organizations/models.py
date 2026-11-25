"""
Organization, Company, Branch, Department, Territory models.

These are the core multi-tenant entities. Everything else in PayReceivio
hangs off Organization → Company → Branch.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import AuditModel, TimeStampedModel


class Organization(AuditModel):
    """Top-level tenant. Each customer business = one Organization."""

    name = models.CharField(_("Name"), max_length=200, db_index=True)
    legal_name = models.CharField(_("Legal name"), max_length=300, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    website = models.URLField(_("Website"), blank=True)
    logo = models.ImageField(_("Logo"), upload_to="org-logos/", null=True, blank=True)
    address_line1 = models.CharField(max_length=300, blank=True)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, blank=True)
    gst_number = models.CharField(max_length=20, blank=True, db_index=True)
    pan_number = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=10, default="INR")
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    is_active = models.BooleanField(default=True, db_index=True)
    subscription_plan = models.CharField(max_length=50, default="trial")
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active", "name"])]

    def __str__(self):
        return self.name

    @property
    def display_address(self):
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.postal_code, self.country]
        return ", ".join(p for p in parts if p)


class Company(AuditModel):
    """Legal entity within an organization. For multi-company businesses."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="companies"
    )
    name = models.CharField(max_length=200, db_index=True)
    legal_name = models.CharField(max_length=300, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gst_number = models.CharField(max_length=20, blank=True, db_index=True)
    pan_number = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=300, blank=True)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=10, default="INR")
    is_active = models.BooleanField(default=True, db_index=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        unique_together = (("organization", "name"),)
        ordering = ["name"]
        indexes = [models.Index(fields=["organization", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Branch(AuditModel):
    """Branch / location within a company."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200, db_index=True)
    code = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=300, blank=True)
    address_line2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_head_office = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        unique_together = (("company", "name"),)
        ordering = ["name"]
        indexes = [models.Index(fields=["company", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Department(AuditModel):
    """Department within an organization - for salesperson/collector grouping."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="departments")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name="departments")
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=20, blank=True)
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="headed_departments",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        unique_together = (("organization", "name"),)
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}"


class Territory(AuditModel):
    """Sales territory - for territory-wise receivables and collection."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="territories")
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=20, blank=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    regions = models.TextField(blank=True, help_text="Comma-separated region names")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Territory")
        verbose_name_plural = _("Territories")
        unique_together = (("organization", "name"),)
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}"

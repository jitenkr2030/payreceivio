"""
Abstract base models shared across the PayReceivio platform.

All tenant-scoped models inherit from TenantOwnedModel which provides:
- organization, company, branch foreign keys (nullable for org-wide data)
- created_at, updated_at, created_by, updated_by audit fields
- is_active soft-delete flag
- proper indexes for tenant isolation
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Provides created_at and updated_at timestamps."""
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """UUID primary key for external-facing entities."""
    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class AuditModel(TimeStampedModel):
    """Tracks who created and updated a record."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name=_("Created by"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name=_("Updated by"),
    )

    class Meta:
        abstract = True


class TenantOwnedModel(AuditModel):
    """
    Multi-tenant base model.

    Every record belongs to an organization. Optionally scoped to a company
    and/or branch for finer-grained tenancy.
    """
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("Organization"),
    )
    company = models.ForeignKey(
        "organizations.Company",
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="+",
        verbose_name=_("Company"),
    )
    branch = models.ForeignKey(
        "organizations.Branch",
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="+",
        verbose_name=_("Branch"),
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["organization", "company"]),
            models.Index(fields=["organization", "company", "branch"]),
        ]


class SoftDeleteModel(models.Model):
    """Soft-delete model. Records are never actually deleted; flagged instead."""
    is_deleted = models.BooleanField(_("Deleted"), default=False, db_index=True)
    deleted_at = models.DateTimeField(_("Deleted at"), null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        verbose_name=_("Deleted by"),
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()


class SingletonModel(models.Model):
    """Singleton pattern for configuration tables."""
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

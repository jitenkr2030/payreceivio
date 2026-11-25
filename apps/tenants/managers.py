"""Query managers that automatically scope queries to a tenant."""
from django.db import models


class TenantManager(models.Manager):
    """Manager that filters by organization."""

    def for_org(self, organization):
        return self.get_queryset().filter(organization=organization)

    def for_company(self, company):
        return self.get_queryset().filter(company=company)

    def for_branch(self, branch):
        return self.get_queryset().filter(branch=branch)


class ActiveTenantManager(TenantManager):
    """Adds default filter for active records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False, is_active=True)

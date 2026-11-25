"""Mixins for views to enforce tenant isolation."""
from django.core.exceptions import PermissionDenied
from django.http import Http404


class TenantMixin:
    """Mixin to ensure request has an active organization and scope querysets."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not getattr(request, "active_organization", None):
            raise PermissionDenied("You do not have access to any organization.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        org = self.request.active_organization
        if hasattr(qs.model, "organization_id"):
            qs = qs.filter(organization=org)
        company = self.request.active_company
        if company and hasattr(qs.model, "company_id") and self.request.GET.get("scope") == "company":
            qs = qs.filter(company=company)
        return qs


class TenantFormMixin:
    """Auto-populate organization/company/branch on form save."""

    def save(self, commit=True):
        instance = super().save(commit=False)
        request = getattr(self, "request", None)
        if request and not getattr(instance, "organization_id", None):
            instance.organization = request.active_organization
        if request and not getattr(instance, "company_id", None) and hasattr(instance, "company_id"):
            instance.company = request.active_company
        if commit:
            instance.save()
            self.save_m2m()
        return instance

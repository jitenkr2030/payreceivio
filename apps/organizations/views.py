"""Organization views - CRUD for org, company, branch, role assignments."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from apps.tenants.mixins import TenantMixin

from .models import Organization, Company, Branch, Department, Territory
from apps.accounts.models import RoleAssignment
from apps.accounts.forms import RoleAssignmentForm


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = "organizations/org_list.html"
    context_object_name = "organizations"

    def get_queryset(self):
        return self.request.user.organizations


class CompanyListView(TenantMixin, ListView):
    model = Company
    template_name = "organizations/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.active_organization)


class BranchListView(TenantMixin, ListView):
    model = Branch
    template_name = "organizations/branch_list.html"
    context_object_name = "branches"

    def get_queryset(self):
        org = self.request.active_organization
        return Branch.objects.filter(company__organization=org)


class RoleAssignmentListView(TenantMixin, ListView):
    model = RoleAssignment
    template_name = "organizations/role_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.active_organization)


class RoleAssignmentCreateView(TenantMixin, CreateView):
    model = RoleAssignment
    form_class = RoleAssignmentForm
    template_name = "organizations/role_form.html"
    success_url = reverse_lazy("organizations:role_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.active_organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.assigned_by = self.request.user
        return super().form_valid(form)


class DepartmentListView(TenantMixin, ListView):
    model = Department
    template_name = "organizations/department_list.html"
    context_object_name = "departments"


class TerritoryListView(TenantMixin, ListView):
    model = Territory
    template_name = "organizations/territory_list.html"
    context_object_name = "territories"

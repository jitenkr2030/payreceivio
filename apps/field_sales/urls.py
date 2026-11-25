"""Field sales views - salesperson dashboard."""
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.urls import path
from django.views.generic import ListView

from apps.tenants.mixins import TenantMixin
from apps.customers.models import Customer
from apps.receivables.models import Invoice
from apps.collections.models import CollectionTask, CollectionVisit, PromiseToPay


class SalespersonDashboardView(TenantMixin, ListView):
    template_name = "sales/dashboard.html"
    context_object_name = "customers"

    def get_queryset(self):
        return Customer.objects.filter(
            organization=self.request.active_organization,
            salesperson=self.request.user,
            is_active=True,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        org = self.request.active_organization
        ctx["open_tasks"] = CollectionTask.objects.filter(
            organization=org, assigned_to=user, status__in=["open", "in_progress"]
        ).order_by("due_date")[:10]
        ctx["today_visits"] = CollectionVisit.objects.filter(
            organization=org, salesperson=user,
            planned_at__date=date.today(),
        )
        ctx["pending_promises"] = PromiseToPay.objects.filter(
            organization=org, status="pending",
            customer__salesperson=user, promised_date__lte=date.today() + timedelta(days=3),
        )
        # Collection today
        today_total = Invoice.objects.filter(
            organization=org, salesperson=user,
            allocations__payment__payment_date=date.today(),
        ).aggregate(t=Sum("allocations__amount"))["t"] or 0
        ctx["collected_today"] = today_total
        return ctx


app_name = "sales"
urlpatterns = [
    path("dashboard/", SalespersonDashboardView.as_view(), name="dashboard"),
]

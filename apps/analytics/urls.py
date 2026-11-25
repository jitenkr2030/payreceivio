"""Analytics views."""
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.views import View

from apps.tenants.mixins import TenantMixin

from .services import (
    compute_kpis, collection_trend, top_debtors,
    salesperson_performance, branch_performance, cash_flow_forecast,
)


class DashboardHomeView(TenantMixin, View):
    """Business owner dashboard."""
    template_name = "analytics/dashboard_owner.html"

    def get(self, request, *args, **kwargs):
        kpis = compute_kpis(request.active_organization)
        trend = collection_trend(request.active_organization, days=30)
        debtors = top_debtors(request.active_organization, n=10)
        sp_perf = salesperson_performance(request.active_organization)
        forecast = cash_flow_forecast(request.active_organization, days=30)
        return render(request, self.template_name, {
            "kpis": kpis,
            "trend": trend,
            "debtors": debtors,
            "salesperson_perf": sp_perf,
            "forecast": forecast[:20],
        })


class FinanceManagerDashboardView(TenantMixin, View):
    template_name = "analytics/dashboard_finance.html"

    def get(self, request, *args, **kwargs):
        kpis = compute_kpis(request.active_organization)
        return render(request, self.template_name, {"kpis": kpis})


class CollectionDashboardView(TenantMixin, View):
    template_name = "analytics/dashboard_collection.html"

    def get(self, request, *args, **kwargs):
        from apps.collections.models import CollectionTask
        from apps.receivables.models import Invoice
        from datetime import date
        open_tasks = CollectionTask.objects.filter(
            organization=request.active_organization,
            status__in=["open", "in_progress"],
        ).count()
        overdue_tasks = CollectionTask.objects.filter(
            organization=request.active_organization,
            status="open",
            due_date__lt=date.today(),
        ).count()
        kpis = compute_kpis(request.active_organization)
        return render(request, self.template_name, {
            "kpis": kpis,
            "open_tasks": open_tasks,
            "overdue_tasks": overdue_tasks,
        })


class DashboardMetricsAPI(View):
    """DRF-style JSON endpoint for dashboard metrics."""
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "auth"}, status=401)
        org = getattr(request, "active_organization", None)
        if not org:
            return JsonResponse({"error": "no_org"}, status=400)
        return JsonResponse(compute_kpis(org))


app_name = "analytics"
urlpatterns = [
    path("metrics/", DashboardMetricsAPI.as_view(), name="metrics"),
    path("reports/owner/", DashboardHomeView.as_view(), name="owner_dashboard"),
    path("reports/finance/", FinanceManagerDashboardView.as_view(), name="finance_dashboard"),
    path("reports/collection/", CollectionDashboardView.as_view(), name="collection_dashboard"),
]

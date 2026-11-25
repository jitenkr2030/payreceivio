"""Subscriptions views."""
from django.urls import path
from django.views.generic import ListView
from apps.tenants.mixins import TenantMixin
from .models import Plan, Subscription, BillingInvoice

app_name = "subscriptions"


class PlanListView(ListView):
    model = Plan
    template_name = "subscriptions/plan_list.html"
    context_object_name = "plans"


class SubscriptionListView(TenantMixin, ListView):
    model = Subscription
    template_name = "subscriptions/subscription_list.html"
    context_object_name = "subscriptions"

    def get_queryset(self):
        return Subscription.objects.filter(organization=self.request.active_organization)


class BillingInvoiceListView(TenantMixin, ListView):
    model = BillingInvoice
    template_name = "subscriptions/billing_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        return BillingInvoice.objects.filter(organization=self.request.active_organization)


urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans"),
    path("", SubscriptionListView.as_view(), name="list"),
    path("billing/", BillingInvoiceListView.as_view(), name="billing"),
]

"""API URL configuration - aggregates all DRF router URLs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api_views import UserViewSet
from apps.organizations.api_views import OrganizationViewSet, CompanyViewSet, BranchViewSet
from apps.customers.api_views import CustomerViewSet
from apps.receivables.api_views import InvoiceViewSet, CreditNoteViewSet
from apps.payments.api_views import PaymentViewSet, PaymentLinkViewSet
from apps.collections.api_views import CollectionTaskViewSet
from apps.reconciliation.api_views import BankTransactionViewSet, ReconciliationViewSet
from apps.communications.api_views import MessageViewSet, CampaignViewSet
from apps.analytics.api_views import DashboardMetricsView
from apps.subscriptions.api_views import SubscriptionViewSet, PlanViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("companies", CompanyViewSet, basename="company")
router.register("branches", BranchViewSet, basename="branch")
router.register("customers", CustomerViewSet, basename="customer")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("credit-notes", CreditNoteViewSet, basename="credit-note")
router.register("payments", PaymentViewSet, basename="payment")
router.register("payment-links", PaymentLinkViewSet, basename="payment-link")
router.register("collection-tasks", CollectionTaskViewSet, basename="collection-task")
router.register("bank-transactions", BankTransactionViewSet, basename="bank-transaction")
router.register("reconciliations", ReconciliationViewSet, basename="reconciliation")
router.register("messages", MessageViewSet, basename="message")
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("plans", PlanViewSet, basename="plan")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/metrics/", DashboardMetricsView.as_view(), name="api-dashboard-metrics"),
    path("auth/", include("rest_framework.urls")),
]

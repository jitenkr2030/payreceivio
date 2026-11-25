"""Project URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.common.urls", namespace="common")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("organizations/", include("apps.organizations.urls", namespace="organizations")),
    path("customers/", include("apps.customers.urls", namespace="customers")),
    path("receivables/", include("apps.receivables.urls", namespace="receivables")),
    path("payments/", include("apps.payments.urls", namespace="payments")),
    path("collections/", include("apps.collections.urls", namespace="collections")),
    path("reconciliation/", include("apps.reconciliation.urls", namespace="reconciliation")),
    path("communications/", include("apps.communications.urls", namespace="communications")),
    path("workflows/", include("apps.workflows.urls", namespace="workflows")),
    path("credit/", include("apps.credit_management.urls", namespace="credit")),
    path("analytics/", include("apps.analytics.urls", namespace="analytics")),
    path("disputes/", include("apps.disputes.urls", namespace="disputes")),
    path("targets/", include("apps.targets.urls", namespace="targets")),
    path("documents/", include("apps.documents.urls", namespace="documents")),
    path("subscriptions/", include("apps.subscriptions.urls", namespace="subscriptions")),
    path("ai/", include("apps.ai_assistant.urls", namespace="ai")),
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("administration/", include("apps.administration.urls", namespace="administration")),
    path("audit/", include("apps.audit.urls", namespace="audit")),
    path("integrations/", include("apps.integrations.urls", namespace="integrations")),
    path("connectors/", include("apps.accounting_connectors.urls", namespace="accounting_connectors")),
    path("tally/", include("apps.tally_connector.urls", namespace="tally")),
    path("zoho/", include("apps.zoho_connector.urls", namespace="zoho")),
    path("portal/", include("apps.customer_portal.urls", namespace="portal")),
    path("sales/", include("apps.field_sales.urls", namespace="sales")),
    path("dashboard/", include("apps.analytics.dashboard_urls", namespace="dashboard")),
    path("api/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        from debug_toolbar.toolbar import debug_toolbar_urls
        urlpatterns = debug_toolbar_urls() + urlpatterns
    except ImportError:
        pass

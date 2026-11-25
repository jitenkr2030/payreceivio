"""Integrations views."""
from django.urls import path
from django.views.generic import ListView, DetailView
from apps.tenants.mixins import TenantMixin
from .models import AccountingConnection, Connector, SyncJob


class ConnectorListView(ListView):
    model = Connector
    template_name = "integrations/connector_list.html"
    context_object_name = "connectors"


class ConnectionListView(TenantMixin, ListView):
    model = AccountingConnection
    template_name = "integrations/connection_list.html"
    context_object_name = "connections"

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.active_organization)


class SyncJobListView(TenantMixin, ListView):
    model = SyncJob
    template_name = "integrations/sync_job_list.html"
    context_object_name = "jobs"
    paginate_by = 50


app_name = "integrations"
urlpatterns = [
    path("connectors/", ConnectorListView.as_view(), name="connector_list"),
    path("connections/", ConnectionListView.as_view(), name="connection_list"),
    path("sync-jobs/", SyncJobListView.as_view(), name="sync_jobs"),
]

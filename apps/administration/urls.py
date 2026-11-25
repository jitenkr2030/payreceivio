"""Administration views."""
from django.urls import path
from django.views.generic import TemplateView, ListView

from apps.tenants.mixins import TenantMixin
from .models import ApiToken, DataExport


class AdminHomeView(TenantMixin, TemplateView):
    template_name = "admin/home.html"


class ApiTokenListView(TenantMixin, ListView):
    model = ApiToken
    template_name = "admin/api_tokens.html"
    context_object_name = "tokens"

    def get_queryset(self):
        return ApiToken.objects.filter(organization=self.request.active_organization)


class DataExportListView(TenantMixin, ListView):
    model = DataExport
    template_name = "admin/data_exports.html"
    context_object_name = "exports"

    def get_queryset(self):
        return DataExport.objects.filter(organization=self.request.active_organization)


app_name = "administration"
urlpatterns = [
    path("", AdminHomeView.as_view(), name="home"),
    path("api-tokens/", ApiTokenListView.as_view(), name="api_tokens"),
    path("exports/", DataExportListView.as_view(), name="exports"),
]

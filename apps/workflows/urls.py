"""Workflows views."""
from django.urls import path
from django.views.generic import ListView

from apps.tenants.mixins import TenantMixin
from .models import Workflow

app_name = "workflows"


class WorkflowListView(TenantMixin, ListView):
    model = Workflow
    template_name = "workflows/workflow_list.html"
    context_object_name = "workflows"


urlpatterns = [
    path("", WorkflowListView.as_view(), name="list"),
]

"""Targets views."""
from django.urls import path
from django.views.generic import ListView
from apps.tenants.mixins import TenantMixin
from .models import CollectionTarget

app_name = "targets"


class TargetListView(TenantMixin, ListView):
    model = CollectionTarget
    template_name = "targets/target_list.html"
    context_object_name = "targets"


urlpatterns = [
    path("", TargetListView.as_view(), name="list"),
]

"""Credit views."""
from django.urls import path
from django.views.generic import ListView
from apps.tenants.mixins import TenantMixin
from .models import CreditAssessment, CreditAlert

app_name = "credit"


class CreditAssessmentListView(TenantMixin, ListView):
    model = CreditAssessment
    template_name = "credit/assessment_list.html"
    context_object_name = "assessments"


class CreditAlertListView(TenantMixin, ListView):
    model = CreditAlert
    template_name = "credit/alert_list.html"
    context_object_name = "alerts"


urlpatterns = [
    path("assessments/", CreditAssessmentListView.as_view(), name="assessment_list"),
    path("alerts/", CreditAlertListView.as_view(), name="alert_list"),
]

"""URLs for audit."""
from django.urls import path
from django.views.generic import ListView

from .models import AuditLog

app_name = "audit"


class AuditLogListView(ListView):
    model = AuditLog
    template_name = "audit/audit_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.all()
        if getattr(self.request, "active_organization", None):
            qs = qs.filter(organization=self.request.active_organization)
        return qs


urlpatterns = [
    path("logs/", AuditLogListView.as_view(), name="logs"),
]

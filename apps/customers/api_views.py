"""Customer DRF API."""
from rest_framework import serializers, viewsets

from .models import Customer, CustomerContact
from apps.tenants.mixins import TenantMixin


class CustomerSerializer(serializers.ModelSerializer):
    outstanding = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ("id", "code", "name", "email", "phone", "gst_number",
                  "credit_limit", "credit_period_days", "risk_category",
                  "salesperson", "territory", "is_active", "outstanding")

    def get_outstanding(self, obj):
        return str(obj.outstanding_balance)


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    filterset_fields = ["salesperson", "territory", "risk_category", "is_active"]
    search_fields = ["code", "name", "phone", "email", "gst_number"]
    ordering_fields = ["name", "code", "created_at"]

    def get_queryset(self):
        qs = Customer.objects.select_related("organization", "salesperson", "territory")
        org = getattr(self.request, "active_organization", None)
        if org:
            qs = qs.filter(organization=org)
        return qs

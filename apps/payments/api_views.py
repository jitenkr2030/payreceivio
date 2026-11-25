"""Payments DRF API."""
from rest_framework import serializers, viewsets

from .models import Payment, PaymentLink


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Payment
        fields = ("id", "payment_number", "customer", "customer_name", "payment_date",
                  "amount", "allocated_amount", "unallocated_amount", "payment_method",
                  "payment_type", "status", "reference", "is_reconciled")


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    filterset_fields = ["customer", "status", "payment_method", "is_reconciled"]
    search_fields = ["payment_number", "customer__name", "reference", "gateway_transaction_id"]
    ordering_fields = ["payment_date", "amount"]

    def get_queryset(self):
        qs = Payment.objects.select_related("customer", "organization")
        org = getattr(self.request, "active_organization", None)
        if org:
            qs = qs.filter(organization=org)
        return qs


class PaymentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLink
        fields = "__all__"


class PaymentLinkViewSet(viewsets.ModelViewSet):
    queryset = PaymentLink.objects.all()
    serializer_class = PaymentLinkSerializer
    filterset_fields = ["customer", "status"]

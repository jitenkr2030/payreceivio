"""Receivables DRF API."""
from decimal import Decimal

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Invoice, CreditNote, DebitNote
from .services import allocate_payment_to_invoices, update_invoice_status


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_code = serializers.CharField(source="customer.code", read_only=True)

    class Meta:
        model = Invoice
        fields = ("id", "invoice_number", "customer", "customer_name", "customer_code",
                  "invoice_date", "due_date", "subtotal", "tax_amount", "total_amount",
                  "paid_amount", "outstanding_amount", "status", "currency",
                  "payment_terms", "salesperson", "is_synced")


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    filterset_fields = ["customer", "status", "salesperson", "is_synced"]
    search_fields = ["invoice_number", "customer__name", "customer__code"]
    ordering_fields = ["invoice_date", "due_date", "total_amount", "outstanding_amount"]

    def get_queryset(self):
        qs = Invoice.objects.select_related("customer", "organization", "salesperson")
        org = getattr(self.request, "active_organization", None)
        if org:
            qs = qs.filter(organization=org)
        return qs

    @action(detail=True, methods=["post"])
    def allocate(self, request, pk=None):
        """Allocate a payment to this invoice."""
        invoice = self.get_object()
        payment_id = request.data.get("payment_id")
        amount = request.data.get("amount")
        if not payment_id or not amount:
            return Response({"detail": "payment_id and amount are required"}, status=400)
        from apps.payments.models import Payment
        payment = Payment.objects.get(pk=payment_id)
        alloc = allocate_payment_to_invoices(payment, [{"invoice_id": invoice.pk, "amount": amount}], request.user)
        return Response({"allocated": str(alloc[0].amount) if alloc else "0"})

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        from .services import get_overdue_invoices
        qs = get_overdue_invoices(getattr(request, "active_organization", None))
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
        fields = "__all__"


class CreditNoteViewSet(viewsets.ModelViewSet):
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    filterset_fields = ["customer", "is_adjusted"]

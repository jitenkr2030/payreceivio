"""Reconciliation API views (separate from admin for clarity)."""
from rest_framework import serializers, viewsets

from .models import BankTransaction, ReconciliationMatch


class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = "__all__"


class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    serializer_class = BankTransactionSerializer
    filterset_fields = ["status", "txn_type", "bank_account"]


class ReconciliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationMatch
        fields = "__all__"


class ReconciliationViewSet(viewsets.ModelViewSet):
    queryset = ReconciliationMatch.objects.all()
    serializer_class = ReconciliationSerializer

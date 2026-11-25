"""Reconciliation admin and API."""
from django.contrib import admin

from .models import BankAccount, BankStatement, BankTransaction, ReconciliationMatch


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("account_name", "bank_name", "account_number", "organization", "is_active")
    list_filter = ("is_active", "organization")


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ("bank_account", "statement_date", "transaction_count", "matched_count", "is_fully_processed")
    list_filter = ("is_fully_processed", "source")


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "txn_type", "amount", "reference_number", "utr_number", "status")
    list_filter = ("status", "txn_type")
    search_fields = ("reference_number", "utr_number", "description", "counterparty")


@admin.register(ReconciliationMatch)
class ReconciliationMatchAdmin(admin.ModelAdmin):
    list_display = ("bank_transaction", "payment", "match_type", "confidence", "approved_at")
    list_filter = ("match_type",)


from rest_framework import serializers, viewsets


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

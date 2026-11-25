"""Reconciliation views."""
from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View

from apps.tenants.mixins import TenantMixin

from .models import BankAccount, BankStatement, BankTransaction, ReconciliationMatch
from .services import import_bank_statement_csv, approve_match, ignore_transaction


class BankAccountListView(TenantMixin, ListView):
    model = BankAccount
    template_name = "reconciliation/bank_list.html"
    context_object_name = "bank_accounts"


class BankStatementListView(TenantMixin, ListView):
    model = BankStatement
    template_name = "reconciliation/statement_list.html"
    context_object_name = "statements"


class UnmatchedTransactionListView(TenantMixin, ListView):
    template_name = "reconciliation/unmatched_list.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        return BankTransaction.objects.filter(
            organization=self.request.active_organization,
            status__in=["unmatched", "suggested"],
            txn_type="credit",
        ).order_by("-transaction_date")


class MatchSuggestionView(TenantMixin, View):
    def get(self, request, pk):
        txn = get_object_or_404(BankTransaction, pk=pk, organization=request.active_organization)
        from apps.payments.models import Payment
        # Find payments with similar amount
        candidates = Payment.objects.filter(
            organization=request.active_organization,
            amount=txn.amount,
            is_reconciled=False,
            status="confirmed",
        )[:10]
        return render(request, "reconciliation/match_suggestions.html",
                      {"txn": txn, "candidates": candidates})

    def post(self, request, pk):
        txn = get_object_or_404(BankTransaction, pk=pk, organization=request.active_organization)
        payment_id = request.POST.get("payment_id")
        from apps.payments.models import Payment
        payment = get_object_or_404(Payment, pk=payment_id, organization=request.active_organization)
        approve_match(txn, payment, user=request.user)
        messages.success(request, "Match approved.")
        return redirect("reconciliation:unmatched")


class ImportStatementView(TenantMixin, CreateView):
    model = BankStatement
    template_name = "reconciliation/import.html"
    fields = ["bank_account", "statement_date"]

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.imported_by = self.request.user
        form.instance.created_by = self.request.user
        form.save()
        return redirect("reconciliation:upload", pk=form.instance.pk)


class UploadStatementView(TenantMixin, View):
    def get(self, request, pk):
        stmt = get_object_or_404(BankStatement, pk=pk, organization=request.active_organization)
        return render(request, "reconciliation/upload.html", {"statement": stmt})

    def post(self, request, pk):
        stmt = get_object_or_404(BankStatement, pk=pk, organization=request.active_organization)
        import csv
        from io import TextIOWrapper
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Please upload a CSV file.")
            return redirect("reconciliation:upload", pk=pk)
        csv_file = TextIOWrapper(file, encoding="utf-8")
        reader = csv.DictReader(csv_file)
        rows = list(reader)
        import_bank_statement_csv(
            organization=request.active_organization,
            bank_account=stmt.bank_account,
            csv_rows=rows,
            statement_date=stmt.statement_date,
            user=request.user,
        )
        messages.success(request, f"Imported {len(rows)} transactions.")
        return redirect("reconciliation:unmatched")


class IgnoreTransactionView(TenantMixin, View):
    def post(self, request, pk):
        txn = get_object_or_404(BankTransaction, pk=pk, organization=request.active_organization)
        ignore_transaction(txn, user=request.user)
        messages.info(request, "Transaction ignored.")
        return redirect("reconciliation:unmatched")


class ReconciliationListView(TenantMixin, ListView):
    model = ReconciliationMatch
    template_name = "reconciliation/match_list.html"
    context_object_name = "matches"

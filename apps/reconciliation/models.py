"""
Reconciliation models - bank accounts, statements, transactions, matches.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantOwnedModel, TimeStampedModel


class BankAccount(TenantOwnedModel):
    """Bank account registered for reconciliation."""

    account_name = models.CharField(max_length=200)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, db_index=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    branch_name = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=10, default="INR")
    is_active = models.BooleanField(default=True)
    last_statement_date = models.DateField(null=True, blank=True)
    last_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = _("Bank account")
        verbose_name_plural = _("Bank accounts")
        unique_together = (("organization", "account_number"),)

    def __str__(self):
        return f"{self.account_name} ({self.account_number})"


class BankStatement(TenantOwnedModel):
    """Uploaded bank statement."""

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="statements")
    statement_date = models.DateField(db_index=True)
    file = models.FileField(upload_to="bank-statements/", null=True, blank=True)
    source = models.CharField(max_length=50, default="csv", choices=[
        ("csv", "CSV"), ("excel", "Excel"), ("api", "Bank API"), ("manual", "Manual")
    ])
    total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    transaction_count = models.PositiveIntegerField(default=0)
    matched_count = models.PositiveIntegerField(default=0)
    unmatched_count = models.PositiveIntegerField(default=0)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    is_fully_processed = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Bank statement")
        verbose_name_plural = _("Bank statements")
        ordering = ["-statement_date"]


class BankTransaction(TenantOwnedModel):
    """A single transaction from a bank statement."""

    TXN_TYPES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]
    STATUS = [
        ("unmatched", "Unmatched"),
        ("suggested", "Suggested"),
        ("matched", "Matched"),
        ("ignored", "Ignored"),
    ]

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="transactions")
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, null=True, blank=True, related_name="transactions")
    transaction_date = models.DateField(db_index=True)
    value_date = models.DateField(null=True, blank=True)
    txn_type = models.CharField(max_length=10, choices=TXN_TYPES, db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=200, blank=True, db_index=True)
    utr_number = models.CharField(max_length=200, blank=True, db_index=True)
    counterparty = models.CharField(max_length=300, blank=True)
    counterparty_account = models.CharField(max_length=50, blank=True)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="unmatched", db_index=True)
    matched_payment = models.ForeignKey("payments.Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="matched_bank_transactions")
    matched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    matched_at = models.DateTimeField(null=True, blank=True)
    match_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Bank transaction")
        verbose_name_plural = _("Bank transactions")
        ordering = ["-transaction_date", "-id"]
        indexes = [
            models.Index(fields=["organization", "status", "-transaction_date"]),
            models.Index(fields=["organization", "utr_number"]),
            models.Index(fields=["organization", "reference_number"]),
        ]

    def __str__(self):
        return f"{self.transaction_date} {self.txn_type} {self.amount} ({self.reference_number or self.description[:30]})"


class ReconciliationMatch(TimeStampedModel):
    """Suggested or confirmed match between a bank transaction and a payment."""

    bank_transaction = models.ForeignKey(BankTransaction, on_delete=models.CASCADE, related_name="matches")
    payment = models.ForeignKey("payments.Payment", on_delete=models.CASCADE, related_name="reconciliation_matches")
    match_type = models.CharField(max_length=20, default="suggested", choices=[
        ("suggested", "Suggested"), ("manual", "Manual"), ("auto", "Auto"), ("approved", "Approved")
    ])
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    match_criteria = models.JSONField(default=dict, help_text="Which fields matched")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Reconciliation match")
        verbose_name_plural = _("Reconciliation matches")
        indexes = [models.Index(fields=["bank_transaction", "payment"])]

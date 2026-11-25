"""
Invoice, InvoiceLine, CreditNote, DebitNote, InvoiceAllocation models.

An Invoice is a sales invoice owed by a customer. InvoiceAllocation links
a Payment to an Invoice (many-to-many) and tracks how much of each invoice
is paid by which payment.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantOwnedModel, TimeStampedModel


class Invoice(TenantOwnedModel):
    """Sales invoice owed by a customer."""

    STATUS = [
        ("draft", "Draft"),
        ("unpaid", "Unpaid"),
        ("partially_paid", "Partially Paid"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    invoice_number = models.CharField(max_length=100, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="invoices")
    invoice_date = models.DateField(db_index=True)
    due_date = models.DateField(db_index=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    adjustment = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, choices=STATUS, default="unpaid", db_index=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    salesperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="invoices",
    )
    accounting_ref = models.CharField(max_length=100, blank=True, help_text="Reference in source accounting system")
    accounting_source = models.CharField(max_length=50, blank=True)
    is_synced = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    pdf_file = models.FileField(upload_to="invoices/", null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        unique_together = (("organization", "invoice_number"),)
        ordering = ["-invoice_date", "-id"]
        indexes = [
            models.Index(fields=["organization", "status", "-invoice_date"]),
            models.Index(fields=["organization", "customer", "-invoice_date"]),
            models.Index(fields=["organization", "due_date"]),
            models.Index(fields=["organization", "salesperson"]),
            models.Index(fields=["organization", "is_synced"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name} - {self.total_amount}"

    def save(self, *args, **kwargs):
        # Recalculate outstanding if not set
        if self.total_amount and self.paid_amount is not None:
            self.outstanding_amount = self.total_amount - self.paid_amount
        # Auto-set status
        if self.status not in ("draft", "cancelled"):
            if self.outstanding_amount <= 0:
                self.status = "paid"
            elif self.paid_amount > 0:
                self.status = "partially_paid"
            elif self.due_date and self.due_date < timezone.now().date():
                self.status = "overdue"
            else:
                self.status = "unpaid"
        super().save(*args, **kwargs)


class InvoiceLine(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1"))
    rate = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = _("Invoice line")
        verbose_name_plural = _("Invoice lines")

    def save(self, *args, **kwargs):
        self.line_total = (self.quantity * self.rate) - self.discount
        if self.tax_rate:
            self.line_total += self.line_total * (self.tax_rate / 100)
        super().save(*args, **kwargs)


class CreditNote(TenantOwnedModel):
    """Credit note issued to a customer."""

    credit_note_number = models.CharField(max_length=100, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="credit_notes")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, null=True, blank=True, related_name="credit_notes")
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_adjusted = models.BooleanField(default=False)
    adjusted_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    accounting_ref = models.CharField(max_length=100, blank=True)
    is_synced = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Credit note")
        verbose_name_plural = _("Credit notes")
        unique_together = (("organization", "credit_note_number"),)
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.credit_note_number} - {self.customer.name}"


class DebitNote(TenantOwnedModel):
    """Debit note - increases customer payable."""

    debit_note_number = models.CharField(max_length=100, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="debit_notes")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, null=True, blank=True, related_name="debit_notes")
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    accounting_ref = models.CharField(max_length=100, blank=True)
    is_synced = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Debit note")
        verbose_name_plural = _("Debit notes")
        unique_together = (("organization", "debit_note_number"),)
        ordering = ["-date", "-id"]


class InvoiceAllocation(TimeStampedModel):
    """Allocation of a Payment against an Invoice."""

    payment = models.ForeignKey("payments.Payment", on_delete=models.CASCADE, related_name="allocations")
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="allocations")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    allocated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    allocation_type = models.CharField(max_length=20, default="manual",
        choices=[("manual", "Manual"), ("auto", "Auto"), ("suggested", "Suggested"), ("approved", "Approved")])
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = _("Invoice allocation")
        verbose_name_plural = _("Invoice allocations")
        indexes = [models.Index(fields=["payment", "invoice"])]

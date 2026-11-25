"""
Payment, PaymentLink, PaymentTransaction, Refund models.

A Payment is a customer payment (received by the business). It can be:
- Allocated to one or more invoices via InvoiceAllocation (in receivables app)
- Linked to a PaymentLink (if collected via payment gateway)
- Tracked as a PaymentTransaction for gateway reconciliation
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantOwnedModel, TimeStampedModel


class Payment(TenantOwnedModel):
    """Customer payment received."""

    PAYMENT_METHODS = [
        ("upi", "UPI"),
        ("neft", "NEFT"),
        ("rtgs", "RTGS"),
        ("imps", "IMPS"),
        ("cheque", "Cheque"),
        ("cash", "Cash"),
        ("card", "Card"),
        ("net_banking", "Net Banking"),
        ("payment_link", "Payment Link"),
        ("payment_gateway", "Payment Gateway"),
        ("credit_note", "Credit Note Adjustment"),
        ("other", "Other"),
    ]

    PAYMENT_TYPES = [
        ("invoice_payment", "Invoice Payment"),
        ("advance", "Advance Payment"),
        ("on_account", "On-Account Payment"),
        ("credit_note_adjustment", "Credit Note Adjustment"),
        ("refund", "Refund"),
    ]

    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    payment_number = models.CharField(max_length=100, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="payments")
    payment_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    unallocated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, db_index=True)
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPES, default="invoice_payment")
    status = models.CharField(max_length=20, choices=STATUS, default="confirmed", db_index=True)
    reference = models.CharField(max_length=200, blank=True, db_index=True, help_text="UTR / Cheque no / Transaction ID")
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    cheque_number = models.CharField(max_length=50, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    payment_link = models.ForeignKey("PaymentLink", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=10, default="INR")
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments_received")
    reconciled_with = models.ForeignKey("reconciliation.BankTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="matched_payments")
    is_reconciled = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=100, blank=True)
    receipt_pdf = models.FileField(upload_to="receipts/", null=True, blank=True)
    accounting_ref = models.CharField(max_length=100, blank=True)
    is_synced = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        unique_together = (("organization", "payment_number"),)
        ordering = ["-payment_date", "-id"]
        indexes = [
            models.Index(fields=["organization", "status", "-payment_date"]),
            models.Index(fields=["organization", "customer", "-payment_date"]),
            models.Index(fields=["organization", "payment_method"]),
            models.Index(fields=["organization", "reference"]),
            models.Index(fields=["organization", "is_reconciled"]),
        ]

    def __str__(self):
        return f"{self.payment_number} - {self.customer.name} - {self.amount}"

    def save(self, *args, **kwargs):
        # Auto-compute unallocated
        if self.allocated_amount is not None:
            self.unallocated_amount = self.amount - self.allocated_amount
        super().save(*args, **kwargs)


class PaymentLink(TenantOwnedModel):
    """Payment link generated for a customer to pay online."""

    STATUS = [
        ("active", "Active"),
        ("paid", "Paid"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    link_id = models.CharField(max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="payment_links")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_links")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    description = models.CharField(max_length=300, blank=True)
    short_url = models.URLField(blank=True)
    qr_code_image = models.ImageField(upload_to="qr-codes/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="active", db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    sent_via = models.CharField(max_length=20, blank=True, help_text="email/sms/whatsapp")
    sent_at = models.DateTimeField(null=True, blank=True)
    gateway_link_id = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = _("Payment link")
        verbose_name_plural = _("Payment links")
        ordering = ["-created_at"]


class PaymentTransaction(TimeStampedModel):
    """Transaction record from payment gateway (webhook payload)."""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True)
    gateway = models.CharField(max_length=50)
    gateway_transaction_id = models.CharField(max_length=200, db_index=True)
    gateway_payment_id = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=50)
    method = models.CharField(max_length=50, blank=True)
    raw_payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Payment transaction")
        verbose_name_plural = _("Payment transactions")
        indexes = [models.Index(fields=["gateway", "gateway_transaction_id"])]


class Refund(TenantOwnedModel):
    """Refund against a payment."""

    refund_number = models.CharField(max_length=100, db_index=True)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    refund_date = models.DateField()
    reason = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, default="pending",
        choices=[("pending", "Pending"), ("processed", "Processed"), ("failed", "Failed")])
    gateway_refund_id = models.CharField(max_length=200, blank=True)
    accounting_ref = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = _("Refund")
        verbose_name_plural = _("Refunds")
        ordering = ["-refund_date"]

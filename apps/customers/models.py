"""
Customer, CustomerContact, CustomerLedgerEntry models.

A customer is a tenant-scoped business that owes money to the organization.
The CustomerLedgerEntry is an immutable ledger of all financial movements
(invoices, payments, credit notes, adjustments) for a customer.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantOwnedModel, TimeStampedModel


class Customer(TenantOwnedModel):
    """Customer master."""

    code = models.CharField(_("Code"), max_length=50, db_index=True)
    name = models.CharField(_("Name"), max_length=300, db_index=True)
    legal_name = models.CharField(_("Legal name"), max_length=300, blank=True)
    customer_type = models.CharField(max_length=20, default="business",
                                     choices=[("individual", "Individual"), ("business", "Business")])
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    gst_number = models.CharField(max_length=20, blank=True, db_index=True)
    pan_number = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    shipping_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, blank=True)

    # Financial attributes
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    credit_period_days = models.PositiveIntegerField(default=30)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    opening_balance_date = models.DateField(null=True, blank=True)

    # Relationships
    salesperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="customers",
    )
    territory = models.ForeignKey(
        "organizations.Territory",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="customers",
    )
    department = models.ForeignKey(
        "organizations.Department",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="customers",
    )

    # Payment preferences
    payment_terms = models.CharField(max_length=100, blank=True)
    preferred_payment_method = models.CharField(max_length=50, blank=True)

    # Comms preferences
    opt_in_email = models.BooleanField(default=True)
    opt_in_sms = models.BooleanField(default=True)
    opt_in_whatsapp = models.BooleanField(default=True)

    # Risk
    risk_category = models.CharField(max_length=20, default="medium",
                                     choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("blocked", "Blocked")])

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        unique_together = (("organization", "code"),)
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "is_active", "name"]),
            models.Index(fields=["organization", "salesperson"]),
            models.Index(fields=["organization", "territory"]),
            models.Index(fields=["organization", "risk_category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def outstanding_balance(self):
        """Calculate current outstanding from ledger entries."""
        result = self.ledger_entries.aggregate(
            total=models.Sum("amount")
        )
        return result["total"] or Decimal("0")

    @property
    def is_over_credit_limit(self):
        return self.outstanding_balance > self.credit_limit and self.credit_limit > 0


class CustomerContact(TenantOwnedModel):
    """Contact person at a customer."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)
    is_accounts_contact = models.BooleanField(default=False)
    department = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = _("Customer contact")
        verbose_name_plural = _("Customer contacts")
        ordering = ["-is_primary", "name"]

    def __str__(self):
        return f"{self.name} ({self.customer.name})"


class CustomerLedgerEntry(TimeStampedModel):
    """
    Immutable ledger of all financial movements for a customer.

    Positive amount = customer owes more (invoice, debit note)
    Negative amount = customer owes less (payment, credit note)
    """

    ENTRY_TYPES = [
        ("opening_balance", "Opening Balance"),
        ("invoice", "Invoice"),
        ("credit_note", "Credit Note"),
        ("debit_note", "Debit Note"),
        ("payment", "Payment"),
        ("refund", "Refund"),
        ("adjustment", "Adjustment"),
        ("interest", "Interest Charge"),
        ("writeoff", "Write Off"),
    ]

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="ledger_entries")
    company = models.ForeignKey("organizations.Company", on_delete=models.PROTECT, null=True, blank=True, related_name="ledger_entries")
    branch = models.ForeignKey("organizations.Branch", on_delete=models.PROTECT, null=True, blank=True, related_name="ledger_entries")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="ledger_entries")
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, db_index=True)
    entry_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=300, blank=True)
    related_invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    related_payment = models.ForeignKey("payments.Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        verbose_name = _("Ledger entry")
        verbose_name_plural = _("Ledger entries")
        ordering = ["-entry_date", "-id"]
        indexes = [
            models.Index(fields=["organization", "customer", "-entry_date"]),
            models.Index(fields=["entry_type", "entry_date"]),
        ]

    def __str__(self):
        return f"{self.entry_date} {self.entry_type} {self.amount} {self.customer.name}"

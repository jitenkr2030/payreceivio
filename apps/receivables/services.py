"""
Receivables services - ageing, status updates, allocation helpers.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from django.db import transaction
from django.db.models import Sum, Q

from .models import Invoice, CreditNote, InvoiceAllocation


def update_invoice_status(invoice: Invoice) -> Invoice:
    """Recompute paid_amount, outstanding_amount and status from allocations."""
    paid = invoice.allocations.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    invoice.paid_amount = paid
    invoice.outstanding_amount = invoice.total_amount - paid
    if invoice.outstanding_amount <= 0:
        invoice.status = "paid"
    elif paid > 0:
        invoice.status = "partially_paid"
    elif invoice.due_date and invoice.due_date < date.today():
        invoice.status = "overdue"
    else:
        invoice.status = "unpaid"
    invoice.save()
    return invoice


def get_overdue_invoices(organization, as_of: date = None):
    as_of = as_of or date.today()
    return Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid", "overdue"],
        due_date__lt=as_of,
        outstanding_amount__gt=0,
    )


def get_invoices_due_today(organization):
    return Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid"],
        due_date=date.today(),
        outstanding_amount__gt=0,
    )


def get_upcoming_invoices(organization, days=7):
    target = date.today() + timedelta(days=days)
    return Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid"],
        due_date__gte=date.today(),
        due_date__lte=target,
        outstanding_amount__gt=0,
    ).order_by("due_date")


def get_invoice_ageing_summary(organization, as_of: date = None):
    """Aggregate ageing buckets across all unpaid invoices."""
    as_of = as_of or date.today()
    buckets = {
        "current": Decimal("0"),
        "1-30": Decimal("0"),
        "31-60": Decimal("0"),
        "61-90": Decimal("0"),
        "91-180": Decimal("0"),
        "180+": Decimal("0"),
    }
    qs = Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid", "overdue"],
        outstanding_amount__gt=0,
    )
    for inv in qs:
        outstanding = inv.outstanding_amount
        if inv.due_date >= as_of:
            buckets["current"] += outstanding
        else:
            days_overdue = (as_of - inv.due_date).days
            if days_overdue <= 30:
                buckets["1-30"] += outstanding
            elif days_overdue <= 60:
                buckets["31-60"] += outstanding
            elif days_overdue <= 90:
                buckets["61-90"] += outstanding
            elif days_overdue <= 180:
                buckets["91-180"] += outstanding
            else:
                buckets["180+"] += outstanding
    buckets["total"] = sum(buckets.values())
    return buckets


def allocate_payment_to_invoices(payment, allocations: List[dict], user=None) -> List[InvoiceAllocation]:
    """
    Allocate a payment across multiple invoices.

    Each item in `allocations` should be {"invoice_id": int, "amount": Decimal/str}.
    Returns the created InvoiceAllocation objects.
    """
    created = []
    with transaction.atomic():
        for alloc in allocations:
            invoice = Invoice.objects.select_for_update().get(pk=alloc["invoice_id"])
            amount = Decimal(str(alloc["amount"]))
            if amount <= 0 or amount > invoice.outstanding_amount + Decimal("0.01"):
                continue
            obj = InvoiceAllocation.objects.create(
                payment=payment, invoice=invoice, amount=amount,
                allocated_by=user, allocation_type="manual",
            )
            update_invoice_status(invoice)
            created.append(obj)
    return created


def generate_invoice_number(organization, company=None, prefix="INV"):
    """Generate the next sequential invoice number."""
    year = date.today().year
    qs = Invoice.objects.filter(organization=organization, invoice_number__startswith=f"{prefix}/{year}/")
    count = qs.count()
    return f"{prefix}/{year}/{count + 1:06d}"


def apply_credit_note_to_invoice(credit_note: CreditNote, invoice: Invoice, amount: Decimal, user=None):
    """Apply a credit note against an invoice (creates an allocation-like adjustment)."""
    from apps.payments.models import Payment
    if amount > credit_note.amount - credit_note.adjusted_amount:
        raise ValueError("Amount exceeds available credit note balance")
    with transaction.atomic():
        # Create a "credit_note" type payment stub
        payment = Payment.objects.create(
            organization=credit_note.organization,
            company=credit_note.company,
            branch=credit_note.branch,
            customer=credit_note.customer,
            payment_date=credit_note.date,
            amount=amount,
            payment_method="credit_note",
            payment_type="credit_note_adjustment",
            reference=credit_note.credit_note_number,
            created_by=user,
        )
        InvoiceAllocation.objects.create(
            payment=payment, invoice=invoice, amount=amount,
            allocated_by=user, allocation_type="manual",
            notes=f"Credit note {credit_note.credit_note_number} applied",
        )
        credit_note.adjusted_amount += amount
        credit_note.is_adjusted = (credit_note.adjusted_amount >= credit_note.amount)
        credit_note.save()
        update_invoice_status(invoice)
    return payment

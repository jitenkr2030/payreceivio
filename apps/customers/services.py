"""
Customer services - ageing, statements, balances.
"""
from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from apps.common.utils import ageing_bucket, ageing_bucket_label

from .models import Customer, CustomerLedgerEntry


def compute_customer_outstanding(customer: Customer, as_of: date = None) -> Decimal:
    """Return the current outstanding balance for a customer as of a date."""
    as_of = as_of or date.today()
    qs = customer.ledger_entries.filter(entry_date__lte=as_of)
    result = qs.aggregate(total=Sum("amount"))
    return result["total"] or Decimal("0")


def compute_customer_ageing(customer: Customer, as_of: date = None) -> dict:
    """
    Compute ageing buckets for a customer based on unpaid invoices.

    Returns a dict like:
      {
        "current": Decimal("12000"),
        "1-30": Decimal("5000"),
        "31-60": Decimal("3000"),
        ...
        "total": Decimal("20000")
      }
    """
    as_of = as_of or date.today()
    buckets = OrderedDict([
        ("current", Decimal("0")),
        ("1-30", Decimal("0")),
        ("31-60", Decimal("0")),
        ("61-90", Decimal("0")),
        ("91-180", Decimal("0")),
        ("180+", Decimal("0")),
    ])

    # Iterate over each unpaid invoice and bucket by overdue days
    from apps.receivables.models import Invoice
    invoices = Invoice.objects.filter(
        customer=customer,
        status__in=["unpaid", "partially_paid", "overdue"],
    )
    for inv in invoices:
        outstanding = inv.outstanding_amount
        if outstanding <= 0:
            continue
        # If invoice not yet due → current
        if inv.due_date >= as_of:
            buckets["current"] += outstanding
        else:
            days_overdue = (as_of - inv.due_date).days
            key = ageing_bucket(days_overdue)
            buckets[key] += outstanding

    buckets["total"] = sum(buckets.values())
    return buckets


def build_customer_statement(customer: Customer, from_date: date = None, to_date: date = None):
    """Build a customer statement: list of ledger entries with running balance."""
    qs = customer.ledger_entries.all()
    if from_date:
        qs = qs.filter(entry_date__gte=from_date)
    if to_date:
        qs = qs.filter(entry_date__lte=to_date)
    qs = qs.order_by("entry_date", "id")

    # Opening balance
    opening_filter = {}
    if from_date:
        opening_filter["entry_date__lt"] = from_date
    opening = customer.ledger_entries.filter(**opening_filter).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    entries = []
    running = opening
    for entry in qs:
        running += entry.amount
        entries.append({
            "date": entry.entry_date,
            "type": entry.entry_type,
            "reference": entry.reference,
            "description": entry.description,
            "debit": entry.amount if entry.amount > 0 else None,
            "credit": -entry.amount if entry.amount < 0 else None,
            "balance": running,
        })

    return {
        "customer": customer,
        "opening_balance": opening,
        "closing_balance": running,
        "entries": entries,
        "from_date": from_date,
        "to_date": to_date,
    }


def bulk_import_customers_from_csv(org, csv_rows):
    """Import customers from CSV rows (dict of headers → values)."""
    created, updated, skipped = [], [], []
    for row in csv_rows:
        code = (row.get("code") or row.get("Code") or "").strip()
        name = (row.get("name") or row.get("Name") or "").strip()
        if not code or not name:
            skipped.append(row)
            continue
        obj, was_created = Customer.objects.update_or_create(
            organization=org, code=code,
            defaults={
                "name": name,
                "email": row.get("email", "").strip(),
                "phone": row.get("phone", "").strip(),
                "gst_number": row.get("gst_number", "").strip(),
                "city": row.get("city", "").strip(),
                "state": row.get("state", "").strip(),
                "credit_limit": Decimal(row.get("credit_limit", "0") or "0"),
                "credit_period_days": int(row.get("credit_period_days", "30") or 30),
            },
        )
        (created if was_created else updated).append(obj)
    return {"created": created, "updated": updated, "skipped": skipped}

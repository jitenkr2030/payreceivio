"""
AI Collections Assistant - rule-based NL query engine.

Parses natural-language questions about receivables and returns
structured answers with cited transactions. No external LLM dependency
for v1; can be upgraded to an LLM-backed implementation later.
"""
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Tuple, List

from django.db.models import Sum, Count, F, Q


def answer_question(question: str, organization, user=None) -> dict:
    """
    Answer a natural-language question about receivables.

    Returns: {"answer": str, "intent": str, "sources": list, "data": dict}
    """
    q = question.lower().strip()
    intent = _classify_intent(q)

    if intent == "total_overdue":
        return _total_overdue(organization)
    elif intent == "top_debtors":
        return _top_debtors(organization, n=20)
    elif intent == "customers_not_paid_within":
        days = _extract_days(q, default=60)
        return _customers_not_paid_within(organization, days)
    elif intent == "expected_collection":
        return _expected_collection_this_week(organization)
    elif intent == "worst_salesperson":
        return _worst_salesperson(organization)
    elif intent == "increasing_delays":
        return _customers_increasing_delays(organization)
    elif intent == "unmatched_transactions":
        return _unmatched_transactions(organization)
    elif intent == "total_outstanding":
        return _total_outstanding(organization)
    elif intent == "dso":
        return _dso(organization)
    else:
        return {
            "answer": (
                "I can help with questions like:\n"
                "- How much money is overdue today?\n"
                "- Which 20 customers have the highest outstanding balances?\n"
                "- Which customers have not paid within 60 days?\n"
                "- What amount should we expect to collect this week?\n"
                "- Which salesperson has the lowest collection performance?\n"
                "- Show customers whose payment delays are increasing.\n"
                "- Which bank transactions have not been matched?\n"
                "- What is our Days Sales Outstanding (DSO)?\n"
            ),
            "intent": "help",
            "sources": [],
            "data": {},
        }


def _classify_intent(q: str) -> str:
    if re.search(r"overdue.*today|today.*overdue|how much.*overdue", q):
        return "total_overdue"
    if re.search(r"top.*debtor|highest.*outstanding|largest.*outstanding", q):
        return "top_debtors"
    if re.search(r"not paid within|not paid in (\d+)", q):
        return "customers_not_paid_within"
    if re.search(r"expect.*collect|collect.*this week|this week.*collect", q):
        return "expected_collection"
    if re.search(r"salesperson.*lowest|worst.*salesperson|salesperson.*performance", q):
        return "worst_salesperson"
    if re.search(r"delay.*increasing|increasing.*delay", q):
        return "increasing_delays"
    if re.search(r"unmatched|not matched", q):
        return "unmatched_transactions"
    if re.search(r"total.*outstanding|outstanding.*total", q):
        return "total_outstanding"
    if re.search(r"dso|days sales outstanding|days.*outstanding", q):
        return "dso"
    return "help"


def _extract_days(q: str, default=60) -> int:
    m = re.search(r"(\d+)\s*days?", q)
    return int(m.group(1)) if m else default


def _total_overdue(org):
    from apps.receivables.models import Invoice
    from apps.receivables.services import get_overdue_invoices
    qs = get_overdue_invoices(org)
    total = qs.aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
    sources = [{"invoice": inv.invoice_number, "customer": inv.customer.name,
                "amount": str(inv.outstanding_amount)} for inv in qs[:10]]
    return {
        "answer": f"Total overdue today: ₹{total:,.2f} across {qs.count()} invoices.",
        "intent": "total_overdue",
        "sources": sources,
        "data": {"total_overdue": str(total), "invoice_count": qs.count()},
    }


def _top_debtors(org, n=20):
    from apps.customers.models import Customer
    qs = Customer.objects.filter(organization=org, is_active=True)
    debtors = []
    for c in qs:
        outstanding = c.outstanding_balance
        if outstanding > 0:
            debtors.append({"id": c.id, "name": c.name, "code": c.code,
                            "outstanding": str(outstanding)})
    debtors.sort(key=lambda x: Decimal(x["outstanding"]), reverse=True)
    top = debtors[:n]
    answer = f"Top {len(top)} debtors by outstanding balance:\n"
    for i, d in enumerate(top, 1):
        answer += f"{i}. {d['name']} ({d['code']}): ₹{Decimal(d['outstanding']):,.2f}\n"
    return {"answer": answer, "intent": "top_debtors", "sources": top, "data": {"count": len(top)}}


def _customers_not_paid_within(org, days):
    from apps.receivables.models import Invoice
    cutoff = date.today() - timedelta(days=days)
    qs = Invoice.objects.filter(
        organization=org,
        status__in=["unpaid", "partially_paid", "overdue"],
        invoice_date__lte=cutoff,
        outstanding_amount__gt=0,
    ).select_related("customer").distinct()
    customers = {}
    for inv in qs:
        if inv.customer_id not in customers:
            customers[inv.customer_id] = {"name": inv.customer.name, "code": inv.customer.code,
                                          "total": Decimal("0"), "invoice_count": 0}
        customers[inv.customer_id]["total"] += inv.outstanding_amount
        customers[inv.customer_id]["invoice_count"] += 1
    sources = list(customers.values())[:20]
    answer = f"Found {len(customers)} customers with invoices unpaid for more than {days} days."
    return {"answer": answer, "intent": "customers_not_paid_within",
            "sources": sources, "data": {"days": days, "count": len(customers)}}


def _expected_collection_this_week(org):
    from apps.receivables.models import Invoice
    today = date.today()
    end = today + timedelta(days=7)
    qs = Invoice.objects.filter(
        organization=org, status__in=["unpaid", "partially_paid"],
        due_date__gte=today, due_date__lte=end,
        outstanding_amount__gt=0,
    )
    total = qs.aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
    return {
        "answer": f"Expected to collect ₹{total:,.2f} this week from {qs.count()} invoices due.",
        "intent": "expected_collection",
        "sources": [{"invoice": i.invoice_number, "customer": i.customer.name,
                     "due_date": i.due_date.isoformat(), "amount": str(i.outstanding_amount)} for i in qs[:10]],
        "data": {"expected": str(total), "invoice_count": qs.count()},
    }


def _worst_salesperson(org):
    from apps.receivables.models import Invoice
    from django.contrib.auth import get_user_model
    User = get_user_model()
    salespeople = User.objects.filter(
        role_assignments__organization=org,
        role_assignments__role__name="salesperson",
    ).distinct()
    worst = None
    worst_score = Decimal("999999")
    for sp in salespeople:
        outstanding = Invoice.objects.filter(
            organization=org, salesperson=sp, outstanding_amount__gt=0
        ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
        if outstanding < worst_score and outstanding > 0:
            worst_score = outstanding
            worst = sp
    if not worst:
        return {"answer": "No salesperson data available.", "intent": "worst_salesperson",
                "sources": [], "data": {}}
    return {
        "answer": f"Lowest collection performance: {worst.display_name} with ₹{worst_score:,.2f} outstanding.",
        "intent": "worst_salesperson",
        "sources": [{"salesperson": worst.display_name, "outstanding": str(worst_score)}],
        "data": {"salesperson": worst.display_name, "outstanding": str(worst_score)},
    }


def _increasing_delays(org):
    from apps.receivables.models import InvoiceAllocation
    from apps.customers.models import Customer
    # Compare avg delay in last 90 days vs previous 90 days
    today = date.today()
    recent_start = today - timedelta(days=90)
    prior_start = today - timedelta(days=180)
    sources = []
    for c in Customer.objects.filter(organization=org, is_active=True):
        recent = InvoiceAllocation.objects.filter(
            invoice__customer=c, payment__payment_date__gte=recent_start
        )
        prior = InvoiceAllocation.objects.filter(
            invoice__customer=c, payment__payment_date__gte=prior_start,
            payment__payment_date__lt=recent_start,
        )
        recent_delays = [(a.payment.payment_date - a.invoice.due_date).days for a in recent if a.invoice.due_date]
        prior_delays = [(a.payment.payment_date - a.invoice.due_date).days for a in prior if a.invoice.due_date]
        if recent_delays and prior_delays:
            recent_avg = sum(recent_delays) / len(recent_delays)
            prior_avg = sum(prior_delays) / len(prior_delays)
            if recent_avg > prior_avg + 5:
                sources.append({"customer": c.name, "recent_avg_delay": round(recent_avg, 1),
                                "prior_avg_delay": round(prior_avg, 1)})
    return {
        "answer": f"Found {len(sources)} customers with increasing payment delays.",
        "intent": "increasing_delays",
        "sources": sources[:20],
        "data": {"count": len(sources)},
    }


def _unmatched_transactions(org):
    from apps.reconciliation.models import BankTransaction
    qs = BankTransaction.objects.filter(
        organization=org, status__in=["unmatched", "suggested"], txn_type="credit"
    )
    total = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    return {
        "answer": f"{qs.count()} unmatched bank transactions worth ₹{total:,.2f} need review.",
        "intent": "unmatched_transactions",
        "sources": [{"date": t.transaction_date.isoformat(), "amount": str(t.amount),
                     "description": t.description[:80]} for t in qs[:10]],
        "data": {"count": qs.count(), "total": str(total)},
    }


def _total_outstanding(org):
    from apps.receivables.models import Invoice
    total = Invoice.objects.filter(
        organization=org, status__in=["unpaid", "partially_paid", "overdue"]
    ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
    return {
        "answer": f"Total outstanding receivables: ₹{total:,.2f}",
        "intent": "total_outstanding",
        "sources": [],
        "data": {"total_outstanding": str(total)},
    }


def _dso(org):
    """Days Sales Outstanding = (Receivables / Annual Sales) * 365"""
    from apps.receivables.models import Invoice
    today = date.today()
    year_ago = today - timedelta(days=365)
    receivables = Invoice.objects.filter(
        organization=org, status__in=["unpaid", "partially_paid", "overdue"]
    ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
    annual_sales = Invoice.objects.filter(
        organization=org, invoice_date__gte=year_ago
    ).aggregate(t=Sum("total_amount"))["t"] or Decimal("1")
    dso = (receivables / annual_sales) * 365 if annual_sales > 0 else 0
    return {
        "answer": f"Days Sales Outstanding (DSO): {dso:.1f} days. (Receivables ₹{receivables:,.2f} / Annual sales ₹{annual_sales:,.2f})",
        "intent": "dso",
        "sources": [],
        "data": {"dso": str(round(dso, 1)), "receivables": str(receivables), "annual_sales": str(annual_sales)},
    }


def draft_reminder_message(customer, invoice=None) -> str:
    """Draft a personalised payment reminder for a customer."""
    name = customer.name.split()[0] if customer.name else "Customer"
    outstanding = customer.outstanding_balance
    if invoice:
        return (
            f"Dear {name},\n\n"
            f"This is a gentle reminder that invoice {invoice.invoice_number} for "
            f"₹{invoice.total_amount:,.2f} was due on {invoice.due_date.isoformat()}. "
            f"Outstanding amount: ₹{invoice.outstanding_amount:,.2f}.\n\n"
            f"Kindly arrange the payment at your earliest convenience. "
            f"If you have already paid, please share the UTR/reference number.\n\n"
            f"Thank you for your business.\n"
            f"- {customer.organization.name if customer.organization else 'PayReceivio'}"
        )
    return (
        f"Dear {name},\n\n"
        f"Our records show an outstanding balance of ₹{outstanding:,.2f} on your account. "
        f"Kindly arrange payment at your earliest convenience.\n\n"
        f"Thank you for your business.\n"
        f"- {customer.organization.name if customer.organization else 'PayReceivio'}"
    )

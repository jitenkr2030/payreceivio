"""Analytics services - KPI computation, reports."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from django.db.models import Sum, Count, Q, F

from apps.receivables.models import Invoice
from apps.receivables.services import get_invoice_ageing_summary
from apps.payments.models import Payment
from apps.customers.models import Customer


def compute_kpis(organization) -> Dict:
    """Compute the dashboard KPIs for an organization."""
    today = date.today()
    month_start = today.replace(day=1)

    # Total receivables
    total_receivables = Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid", "overdue"],
    ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")

    # Total overdue
    overdue_invoices = Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid", "overdue"],
        due_date__lt=today,
        outstanding_amount__gt=0,
    )
    total_overdue = overdue_invoices.aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")

    # Collected this month
    collected_month = Payment.objects.filter(
        organization=organization,
        payment_date__gte=month_start,
        payment_date__lte=today,
        status="confirmed",
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    # Collected today
    collected_today = Payment.objects.filter(
        organization=organization,
        payment_date=today,
        status="confirmed",
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

    # Overdue customer count
    overdue_customer_count = overdue_invoices.values("customer_id").distinct().count()

    # Unallocated payments
    unallocated = Payment.objects.filter(
        organization=organization, status="confirmed",
    ).aggregate(t=Sum("unallocated_amount"))["t"] or Decimal("0")

    # Average collection period (DSO)
    year_ago = today - timedelta(days=365)
    annual_sales = Invoice.objects.filter(
        organization=organization, invoice_date__gte=year_ago
    ).aggregate(t=Sum("total_amount"))["t"] or Decimal("1")
    dso = (total_receivables / annual_sales) * 365 if annual_sales > 0 else 0

    # Collection efficiency
    total_invoiced_month = Invoice.objects.filter(
        organization=organization, invoice_date__gte=month_start
    ).aggregate(t=Sum("total_amount"))["t"] or Decimal("0")
    efficiency = (collected_month / total_invoiced_month * 100) if total_invoiced_month > 0 else 0

    # Payment success rate
    total_payments = Payment.objects.filter(organization=organization).count()
    successful_payments = Payment.objects.filter(organization=organization, status="confirmed").count()
    success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0

    # Upcoming receivables (next 7 days)
    upcoming = Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid"],
        due_date__gte=today,
        due_date__lte=today + timedelta(days=7),
        outstanding_amount__gt=0,
    ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")

    return {
        "total_receivables": total_receivables,
        "total_overdue": total_overdue,
        "collected_this_month": collected_month,
        "collected_today": collected_today,
        "upcoming_receivables_7d": upcoming,
        "overdue_customer_count": overdue_customer_count,
        "unallocated_payments": unallocated,
        "dso": dso,
        "collection_efficiency": efficiency,
        "payment_success_rate": success_rate,
        "ageing_summary": get_invoice_ageing_summary(organization),
    }


def collection_trend(organization, days=30) -> List[Dict]:
    """Daily collection trend for last N days."""
    today = date.today()
    start = today - timedelta(days=days)
    payments = Payment.objects.filter(
        organization=organization,
        payment_date__gte=start,
        status="confirmed",
    ).values("payment_date").annotate(total=Sum("amount")).order_by("payment_date")
    return [{"date": p["payment_date"].isoformat(), "amount": float(p["total"])} for p in payments]


def top_debtors(organization, n=10) -> List[Dict]:
    """Top N customers by outstanding balance."""
    customers = Customer.objects.filter(organization=organization, is_active=True)
    debtors = []
    for c in customers:
        outstanding = c.outstanding_balance
        if outstanding > 0:
            debtors.append({"id": c.id, "name": c.name, "code": c.code, "outstanding": float(outstanding)})
    debtors.sort(key=lambda x: x["outstanding"], reverse=True)
    return debtors[:n]


def salesperson_performance(organization) -> List[Dict]:
    """Collection performance by salesperson."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    salespeople = User.objects.filter(
        role_assignments__organization=organization,
        role_assignments__role__name="salesperson",
    ).distinct()
    result = []
    for sp in salespeople:
        outstanding = Invoice.objects.filter(
            organization=organization, salesperson=sp, outstanding_amount__gt=0
        ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
        collected = Payment.objects.filter(
            organization=organization, received_by=sp, status="confirmed",
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        customer_count = Customer.objects.filter(
            organization=organization, salesperson=sp
        ).count()
        result.append({
            "id": sp.id, "name": sp.display_name,
            "outstanding": float(outstanding),
            "collected": float(collected),
            "customer_count": customer_count,
        })
    return result


def branch_performance(organization) -> List[Dict]:
    """Collection performance by branch."""
    from apps.organizations.models import Branch
    branches = Branch.objects.filter(company__organization=organization, is_active=True)
    result = []
    for b in branches:
        outstanding = Invoice.objects.filter(
            organization=organization, branch=b, outstanding_amount__gt=0
        ).aggregate(t=Sum("outstanding_amount"))["t"] or Decimal("0")
        collected = Payment.objects.filter(
            organization=organization, branch=b, status="confirmed",
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        result.append({
            "id": b.id, "name": b.name,
            "outstanding": float(outstanding),
            "collected": float(collected),
        })
    return result


def cash_flow_forecast(organization, days=30) -> List[Dict]:
    """Forecast expected collections from invoices due in next N days."""
    today = date.today()
    end = today + timedelta(days=days)
    invoices = Invoice.objects.filter(
        organization=organization,
        status__in=["unpaid", "partially_paid"],
        due_date__gte=today,
        due_date__lte=end,
        outstanding_amount__gt=0,
    ).order_by("due_date")
    return [{"date": inv.due_date.isoformat(), "amount": float(inv.outstanding_amount),
             "invoice": inv.invoice_number, "customer": inv.customer.name} for inv in invoices]

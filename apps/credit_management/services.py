"""Credit management services - scoring, alerts."""
from datetime import date
from decimal import Decimal
from django.db.models import Sum, Avg

from .models import CreditAssessment, CreditAlert


def compute_payment_reliability_score(customer) -> Decimal:
    """Compute a 0-100 payment reliability score for a customer."""
    payments = customer.payments.all()
    if not payments.exists():
        return Decimal("50")  # Neutral score for new customers
    # Average delay: days between invoice due_date and payment date
    from apps.receivables.models import InvoiceAllocation
    allocs = InvoiceAllocation.objects.filter(payment__customer=customer)
    delays = []
    for alloc in allocs:
        if alloc.invoice.due_date and alloc.payment.payment_date:
            delay = (alloc.payment.payment_date - alloc.invoice.due_date).days
            delays.append(max(0, delay))
    if not delays:
        return Decimal("70")
    avg_delay = sum(delays) / len(delays)
    # Score: 0 delay = 100, 30 days = 70, 60 days = 40, 90+ = 10
    if avg_delay <= 0:
        score = Decimal("100")
    elif avg_delay <= 30:
        score = Decimal("100") - Decimal(str(avg_delay))
    elif avg_delay <= 60:
        score = Decimal("70") - Decimal(str(avg_delay - 30))
    elif avg_delay <= 90:
        score = Decimal("40") - Decimal(str(avg_delay - 60))
    else:
        score = Decimal("10")
    return max(score, Decimal("0"))


def assess_customer_credit(customer, user=None) -> CreditAssessment:
    """Create a credit assessment snapshot for a customer."""
    from apps.customers.services import compute_customer_ageing
    ageing = compute_customer_ageing(customer)
    overdue = sum(v for k, v in ageing.items() if k != "current" and k != "total")
    score = compute_payment_reliability_score(customer)
    if score >= 80:
        risk = "low"
    elif score >= 60:
        risk = "medium"
    elif score >= 30:
        risk = "high"
    else:
        risk = "blocked"
    return CreditAssessment.objects.create(
        organization=customer.organization,
        customer=customer,
        assessment_date=date.today(),
        outstanding_amount=customer.outstanding_balance,
        overdue_amount=overdue,
        payment_reliability_score=score,
        risk_category=risk,
        recommended_limit=customer.credit_limit,
        assessed_by=user,
        factors={"ageing": {k: str(v) for k, v in ageing.items()},
                 "score": str(score), "risk": risk},
    )


def check_credit_alerts(customer):
    """Check and create credit alerts for a customer."""
    alerts = []
    if customer.credit_limit > 0 and customer.outstanding_balance > customer.credit_limit:
        alert, created = CreditAlert.objects.get_or_create(
            organization=customer.organization,
            customer=customer,
            alert_type="limit_breach",
            is_acknowledged=False,
            defaults={
                "severity": "critical",
                "message": f"Outstanding ₹{customer.outstanding_balance} exceeds credit limit ₹{customer.credit_limit}",
            },
        )
        if created:
            alerts.append(alert)
    return alerts

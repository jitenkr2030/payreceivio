"""Celery task definitions for PayReceivio.

These tasks are auto-discovered by Celery. They can be run via:
- Celery worker (production): `celery -A config worker -l info`
- Synchronous (dev with CELERY_TASK_ALWAYS_EAGER=True): called directly
"""
from celery import shared_task
from django.utils import timezone


@shared_task
def process_scheduled_messages_task():
    """Send messages whose scheduled_at has passed."""
    from apps.communications.services import process_scheduled_messages
    process_scheduled_messages()
    return "scheduled_messages_processed"


@shared_task
def send_reminder_sequence_task():
    """Run the reminder sequence for all overdue invoices."""
    from apps.receivables.models import Invoice
    from apps.communications.services import send_reminder_sequence
    qs = Invoice.objects.filter(
        status__in=["unpaid", "partially_paid", "overdue"],
        outstanding_amount__gt=0,
    )
    count = 0
    for inv in qs:
        try:
            send_reminder_sequence(inv)
            count += 1
        except Exception:
            pass
    return f"reminder_sequence_run_for_{count}_invoices"


@shared_task
def auto_match_reconciliation_task():
    """Run auto-matching for unmatched bank transactions."""
    from apps.reconciliation.services import auto_match_transactions
    from apps.organizations.models import Organization
    total = 0
    for org in Organization.objects.filter(is_active=True):
        auto_match_transactions(org)
        total += 1
    return f"auto_match_run_for_{total}_organizations"


@shared_task
def sync_accounting_connections_task():
    """Process pending accounting syncs."""
    from apps.integrations.services import process_pending_syncs
    process_pending_syncs()
    return "accounting_syncs_processed"


@shared_task
def compute_daily_metrics_task():
    """Snapshot collection metrics for analytics."""
    from datetime import date
    from django.db.models import Sum
    from apps.targets.models import CollectionMetric
    from apps.organizations.models import Organization
    from apps.payments.models import Payment
    from apps.receivables.models import Invoice
    today = date.today()
    for org in Organization.objects.filter(is_active=True):
        # Per salesperson
        for sp in org.role_assignments.filter(role__name="salesperson").select_related("user"):
            collected = Payment.objects.filter(
                organization=org, received_by=sp.user, payment_date=today, status="confirmed"
            ).aggregate(t=Sum("amount"))["t"] or 0
            inv_count = Invoice.objects.filter(organization=org, salesperson=sp.user, status="overdue").count()
            CollectionMetric.objects.create(
                organization=org,
                metric_date=today,
                salesperson=sp.user,
                total_collected=collected,
                invoice_count=inv_count,
                overdue_count=inv_count,
                created_by=sp.user, updated_by=sp.user,
            )
    return f"daily_metrics_computed_for_{today}"


@shared_task
def check_credit_alerts_task():
    """Run credit alert checks for all customers."""
    from apps.credit_management.services import check_credit_alerts
    from apps.customers.models import Customer
    total = 0
    for c in Customer.objects.filter(is_active=True):
        alerts = check_credit_alerts(c)
        total += len(alerts)
    return f"credit_alerts_checked_{total}_created"


@shared_task
def update_invoice_status_task():
    """Recompute status for all unpaid invoices (overdue detection)."""
    from apps.receivables.models import Invoice
    qs = Invoice.objects.filter(status__in=["unpaid", "partially_paid"])
    count = 0
    for inv in qs:
        old_status = inv.status
        inv.save()  # triggers auto-status update
        if inv.status != old_status:
            count += 1
    return f"invoice_status_updated_{count}_changed"

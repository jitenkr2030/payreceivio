"""Sync services - orchestrate synchronization jobs."""
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import AccountingConnection, SyncJob, SyncLog, SyncError
from .base import get_connector


@transaction.atomic
def run_sync(connection: AccountingConnection, entity_type="", user=None, is_manual=False) -> SyncJob:
    """Create and run a sync job."""
    job = SyncJob.objects.create(
        connection=connection,
        direction="import",
        status="running",
        entity_type=entity_type,
        started_at=timezone.now(),
        triggered_by=user,
        is_manual=is_manual,
    )
    try:
        connector = get_connector(connection.connector.name)
        connector.authenticate(connection)

        if not entity_type or entity_type == "customer":
            customers = connector.fetch_customers(connection)
            job.records_processed += len(customers)
            SyncLog.objects.create(job=job, level="info", entity_type="customer",
                                   message=f"Fetched {len(customers)} customers")

        if not entity_type or entity_type == "invoice":
            invoices = connector.fetch_invoices(connection)
            job.records_processed += len(invoices)
            SyncLog.objects.create(job=job, level="info", entity_type="invoice",
                                   message=f"Fetched {len(invoices)} invoices")

        if not entity_type or entity_type == "receipt":
            receipts = connector.fetch_receipts(connection)
            job.records_processed += len(receipts)

        job.status = "completed"
        job.completed_at = timezone.now()
        connection.last_sync_at = timezone.now()
        connection.last_sync_status = "completed"
        connection.last_sync_records = job.records_processed
        connection.save()
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = timezone.now()
        connection.last_sync_status = "failed"
        connection.save()
        SyncLog.objects.create(job=job, level="error", message=str(e))
    job.save()
    return job


def schedule_next_sync(connection: AccountingConnection):
    """Compute the next sync time based on frequency."""
    if connection.sync_frequency == "manual":
        return
    now = timezone.now()
    delta = {"hourly": timedelta(hours=1), "daily": timedelta(days=1), "weekly": timedelta(weeks=1)}.get(connection.sync_frequency, timedelta(hours=1))
    connection.next_sync_at = now + delta
    connection.save()


def process_pending_syncs():
    """Process all connections due for sync."""
    qs = AccountingConnection.objects.filter(
        is_active=True, status="active",
        next_sync_at__lte=timezone.now(),
    )
    for conn in qs:
        run_sync(conn)
        schedule_next_sync(conn)

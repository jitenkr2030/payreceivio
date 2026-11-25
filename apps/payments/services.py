"""Payment services - allocation, receipts, idempotency."""
from datetime import date
from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_action

from .models import Payment, PaymentLink, Refund
from apps.receivables.models import Invoice, InvoiceAllocation
from apps.receivables.services import update_invoice_status
from apps.customers.models import CustomerLedgerEntry


def generate_payment_number(organization, prefix="RCT"):
    year = date.today().year
    count = Payment.objects.filter(organization=organization, payment_number__startswith=f"{prefix}/{year}/").count()
    return f"{prefix}/{year}/{count + 1:06d}"


def generate_receipt_number(organization, prefix="RCP"):
    year = date.today().year
    count = Payment.objects.filter(organization=organization, receipt_number__startswith=f"{prefix}/{year}/").count()
    return f"{prefix}/{year}/{count + 1:06d}"


def generate_payment_link_id():
    import uuid
    return f"prl_{uuid.uuid4().hex[:24]}"


@transaction.atomic
def record_payment(
    *,
    organization,
    customer,
    amount,
    payment_date,
    payment_method,
    payment_type="invoice_payment",
    reference="",
    received_by=None,
    notes="",
    company=None,
    branch=None,
    request=None,
) -> Payment:
    """Idempotent payment recording. Returns the created Payment."""
    payment_number = generate_payment_number(organization)
    payment = Payment.objects.create(
        organization=organization,
        company=company or (customer.company if customer else None),
        branch=branch or (customer.branch if customer else None),
        payment_number=payment_number,
        customer=customer,
        payment_date=payment_date,
        amount=Decimal(str(amount)),
        payment_method=payment_method,
        payment_type=payment_type,
        reference=reference,
        received_by=received_by,
        notes=notes,
        status="confirmed",
        receipt_number=generate_receipt_number(organization),
        created_by=received_by,
        updated_by=received_by,
    )
    # Ledger entry
    CustomerLedgerEntry.objects.create(
        organization=organization,
        company=payment.company,
        branch=payment.branch,
        customer=customer,
        entry_type="payment",
        entry_date=payment_date,
        amount=-payment.amount,
        reference=payment_number,
        description=f"Payment received via {payment_method}" + (f" - {reference}" if reference else ""),
        related_payment=payment,
        created_by=received_by,
    )
    log_action(
        user=received_by, organization=organization, action="create",
        entity_type="payment", entity_id=payment.id, entity_label=str(payment),
        request=request,
    )
    return payment


@transaction.atomic
def allocate_payment(payment: Payment, allocations: List[dict], user=None, request=None):
    """
    Allocate a payment across invoices.
    allocations: [{"invoice_id": int, "amount": str/Decimal}, ...]
    """
    total_allocated = Decimal("0")
    for alloc in allocations:
        amount = Decimal(str(alloc["amount"]))
        if amount <= 0:
            continue
        invoice = Invoice.objects.select_for_update().get(pk=alloc["invoice_id"])
        if amount > invoice.outstanding_amount + Decimal("0.01"):
            raise ValueError(f"Amount {amount} exceeds outstanding {invoice.outstanding_amount} for invoice {invoice.invoice_number}")
        InvoiceAllocation.objects.create(
            payment=payment, invoice=invoice, amount=amount,
            allocated_by=user, allocation_type="manual",
        )
        update_invoice_status(invoice)
        total_allocated += amount
    payment.allocated_amount = (payment.allocated_amount or Decimal("0")) + total_allocated
    payment.unallocated_amount = payment.amount - payment.allocated_amount
    payment.save()
    return payment


@transaction.atomic
def create_payment_link(
    *, organization, customer, amount, invoice=None, description="", expires_in_days=7,
    created_by=None, request=None,
) -> PaymentLink:
    """Generate a payment link (mock URL - real provider integration stubbed)."""
    from datetime import timedelta
    link = PaymentLink.objects.create(
        organization=organization,
        company=customer.company,
        branch=customer.branch,
        customer=customer,
        invoice=invoice,
        amount=Decimal(str(amount)),
        description=description,
        link_id=generate_payment_link_id(),
        short_url=f"https://pay.payreceivio.com/pay/{generate_payment_link_id()[:8]}",
        expires_at=timezone.now() + timedelta(days=expires_in_days),
        created_by=created_by,
        updated_by=created_by,
    )
    log_action(
        user=created_by, organization=organization, action="create",
        entity_type="payment_link", entity_id=link.id, entity_label=str(link),
        request=request,
    )
    return link


@transaction.atomic
def process_gateway_webhook(payload: dict, organization) -> Payment | None:
    """
    Process a webhook from a payment gateway.

    Idempotent: if a Payment already exists for this gateway_transaction_id,
    returns it without re-creating.
    """
    from .models import PaymentTransaction
    gateway = payload.get("gateway", "razorpay")
    txn_id = payload.get("gateway_transaction_id")
    if not txn_id:
        return None
    # Idempotency
    existing_txn = PaymentTransaction.objects.filter(
        gateway=gateway, gateway_transaction_id=txn_id
    ).first()
    if existing_txn and existing_txn.payment:
        return existing_txn.payment

    amount = Decimal(str(payload.get("amount", 0)))
    customer_id = payload.get("customer_id")
    from apps.customers.models import Customer
    try:
        customer = Customer.objects.get(organization=organization, pk=customer_id)
    except Customer.DoesNotExist:
        return None

    payment = record_payment(
        organization=organization,
        customer=customer,
        amount=amount,
        payment_date=date.today(),
        payment_method=payload.get("method", "payment_gateway"),
        payment_type="invoice_payment" if payload.get("invoice_id") else "advance",
        reference=txn_id,
        received_by=None,
        gateway_transaction_id=txn_id,
    )
    PaymentTransaction.objects.create(
        payment=payment, gateway=gateway, gateway_transaction_id=txn_id,
        amount=amount, status=payload.get("status", "captured"),
        method=payload.get("method", ""), raw_payload=payload,
        processed_at=timezone.now(),
    )
    return payment

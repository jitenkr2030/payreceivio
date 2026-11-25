"""
Communications services - template rendering, channel senders, scheduler.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.utils import timezone

from .models import Message, MessageTemplate, Campaign


def render_template(template_body: str, context: dict) -> str:
    """Render a template string with the given context."""
    return Template(template_body).render(Context(context))


def build_message_context(customer=None, invoice=None, payment=None, organization=None) -> dict:
    """Build the standard context for template rendering."""
    ctx = {
        "organization_name": organization.name if organization else "PayReceivio",
        "today": date.today().isoformat(),
        "currency_symbol": settings.PAYRECEIVIO["CURRENCY_SYMBOL"],
    }
    if customer:
        ctx.update({
            "customer_name": customer.name,
            "customer_code": customer.code,
            "customer_email": customer.email,
            "customer_phone": customer.phone,
            "customer_outstanding": str(customer.outstanding_balance),
        })
    if invoice:
        ctx.update({
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "invoice_amount": str(invoice.total_amount),
            "outstanding_amount": str(invoice.outstanding_amount),
            "days_overdue": (date.today() - invoice.due_date).days if invoice.due_date < date.today() else 0,
        })
    if payment:
        ctx.update({
            "payment_number": payment.payment_number,
            "payment_amount": str(payment.amount),
            "payment_date": payment.payment_date.isoformat(),
            "payment_method": payment.get_payment_method_display(),
            "receipt_number": payment.receipt_number,
        })
    return ctx


def queue_message(*, organization, customer=None, template=None, channel="email",
                  to_address="", subject="", body="", scheduled_at=None,
                  invoice=None, payment=None, sent_by=None, request=None) -> Message:
    """Create a Message record in 'queued' status, ready for the sender."""
    if template:
        ctx = build_message_context(customer=customer, invoice=invoice, payment=payment, organization=organization)
        subject = render_template(template.subject or "", ctx)
        body = render_template(template.body, ctx)
    message = Message.objects.create(
        organization=organization,
        company=customer.company if customer else None,
        branch=customer.branch if customer else None,
        customer=customer, invoice=invoice, payment=payment,
        template=template, channel=channel,
        to_address=to_address, subject=subject, body=body,
        status="queued" if not scheduled_at else "draft",
        scheduled_at=scheduled_at,
        sent_by=sent_by,
        created_by=sent_by, updated_by=sent_by,
    )
    return message


def send_message(message: Message) -> bool:
    """Actually send the message via the configured channel."""
    try:
        if message.channel == "email":
            send_mail(
                subject=message.subject,
                message=message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message.to_address],
                fail_silently=False,
            )
        elif message.channel == "sms":
            _send_sms(message.to_address, message.body)
        elif message.channel == "whatsapp":
            _send_whatsapp(message.to_address, message.body, message.subject)
        message.status = "sent"
        message.sent_at = timezone.now()
        message.save()
        return True
    except Exception as e:
        message.status = "failed"
        message.error_message = str(e)
        message.retry_count += 1
        message.save()
        return False


def _send_sms(to, body):
    """Stub SMS sender - replace with real provider integration."""
    # Real implementation would call an Indian SMS provider API
    import logging
    logging.getLogger("payreceivio").info(f"[SMS] To: {to}, Body: {body}")


def _send_whatsapp(to, body, template_name=None):
    """Stub WhatsApp sender - replace with WhatsApp Business Platform."""
    import logging
    logging.getLogger("payreceivio").info(f"[WA] To: {to}, Body: {body}")


def process_scheduled_messages():
    """Send any messages whose scheduled_at has passed."""
    qs = Message.objects.filter(
        status="queued",
        scheduled_at__lte=timezone.now(),
    )
    for message in qs:
        send_message(message)


def send_reminder_sequence(invoice):
    """Send the appropriate reminder based on days-overdue, per the configured schedule."""
    from apps.receivables.models import Invoice
    if not isinstance(invoice, Invoice):
        return
    if invoice.outstanding_amount <= 0:
        return
    days_overdue = (date.today() - invoice.due_date).days
    # Find the matching schedule entry
    schedule = settings.PAYRECEIVIO["REMINDER_SCHEDULE"]
    matched = None
    for offset, label in schedule:
        if offset == days_overdue:
            matched = (offset, label)
            break
    if not matched:
        return
    _, label = matched
    # Pick a template by category
    category = "overdue_reminder" if days_overdue > 0 else "invoice_reminder"
    template = MessageTemplate.objects.filter(
        organization=invoice.organization, category=category, channel="whatsapp", is_active=True
    ).first()
    if not template:
        return
    to = invoice.customer.whatsapp_number or invoice.customer.phone
    if not to:
        return
    queue_message(
        organization=invoice.organization,
        customer=invoice.customer,
        invoice=invoice,
        template=template,
        channel="whatsapp",
        to_address=to,
        sent_by=None,
    )

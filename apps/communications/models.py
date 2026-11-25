"""
Communications models - templates, messages, campaigns, conversations.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantOwnedModel, TimeStampedModel


class MessageTemplate(TenantOwnedModel):
    """Reusable message template for email/SMS/WhatsApp."""

    CHANNELS = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("whatsapp", "WhatsApp"),
    ]
    CATEGORIES = [
        ("invoice_reminder", "Invoice Reminder"),
        ("overdue_reminder", "Overdue Reminder"),
        ("payment_confirmation", "Payment Confirmation"),
        ("statement_share", "Statement Share"),
        ("receipt_share", "Receipt Share"),
        ("payment_link", "Payment Link"),
        ("escalation", "Escalation"),
        ("welcome", "Welcome"),
        ("custom", "Custom"),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORIES, default="custom")
    channel = models.CharField(max_length=20, choices=CHANNELS, db_index=True)
    subject = models.CharField(max_length=300, blank=True, help_text="Email subject / WhatsApp template name")
    body = models.TextField(help_text="Template body. Use {{variables}} for substitution.")
    variables = models.JSONField(default=list, blank=True, help_text="List of variable names supported")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True, help_text="WhatsApp template approval timestamp")

    class Meta:
        verbose_name = _("Message template")
        verbose_name_plural = _("Message templates")
        ordering = ["name"]
        indexes = [models.Index(fields=["organization", "channel", "category", "is_active"])]


class Message(TenantOwnedModel):
    """A single message sent (or scheduled to send)."""

    STATUS = [
        ("draft", "Draft"),
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
        ("failed", "Failed"),
        ("bounced", "Bounced"),
        ("cancelled", "Cancelled"),
    ]

    template = models.ForeignKey(MessageTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, null=True, blank=True, related_name="messages")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")
    payment = models.ForeignKey("payments.Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")
    channel = models.CharField(max_length=20, choices=MessageTemplate.CHANNELS, db_index=True)
    to_address = models.CharField(max_length=300)
    cc_address = models.CharField(max_length=300, blank=True)
    subject = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    rendered_body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft", db_index=True)
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    gateway_message_id = models.CharField(max_length=300, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_messages")
    campaign = models.ForeignKey("Campaign", on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status", "-created_at"]),
            models.Index(fields=["organization", "channel", "-sent_at"]),
            models.Index(fields=["scheduled_at"]),
        ]


class Campaign(TenantOwnedModel):
    """Bulk messaging campaign."""

    STATUS = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    name = models.CharField(max_length=200)
    template = models.ForeignKey(MessageTemplate, on_delete=models.PROTECT, related_name="campaigns")
    channel = models.CharField(max_length=20, choices=MessageTemplate.CHANNELS)
    audience_filter = models.JSONField(default=dict, help_text="Filter criteria for recipients")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="draft", db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="campaigns")

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-created_at"]


class Conversation(TenantOwnedModel):
    """Conversation thread with a customer (WhatsApp/email)."""

    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="conversations")
    channel = models.CharField(max_length=20, choices=MessageTemplate.CHANNELS)
    external_id = models.CharField(max_length=300, blank=True, help_text="WhatsApp conversation ID / email thread ID")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    status = models.CharField(max_length=20, default="open", choices=[
        ("open", "Open"), ("pending", "Pending Customer Reply"), ("closed", "Closed")
    ])
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ["-last_message_at"]


class ConversationMessage(TimeStampedModel):
    """Individual message in a conversation (inbound or outbound)."""

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="thread")
    direction = models.CharField(max_length=10, choices=[("in", "Inbound"), ("out", "Outbound")])
    body = models.TextField()
    external_message_id = models.CharField(max_length=300, blank=True)
    sender = models.CharField(max_length=200, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

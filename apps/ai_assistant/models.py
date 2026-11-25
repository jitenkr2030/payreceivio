"""AI Assistant models."""
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class Conversation(TenantOwnedModel):
    """Chat conversation with the AI assistant."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations")
    title = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)


class Message(models.Model):
    """Individual chat message."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=[("user", "User"), ("assistant", "Assistant")])
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True)
    sources = models.JSONField(default=list, blank=True, help_text="Cited transactions")
    created_at = models.DateTimeField(auto_now_add=True)

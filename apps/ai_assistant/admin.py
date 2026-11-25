"""AI assistant admin."""
from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "title", "is_active", "last_message_at")


@admin.register(Message)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "intent", "created_at")

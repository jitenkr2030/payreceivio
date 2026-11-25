"""Notifications admin and service."""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notif_type", "title", "is_read", "created_at")
    list_filter = ("is_read", "notif_type")


def create_notification(*, organization, user, notif_type, title, message,
                       entity_type="", entity_id="", action_url=""):
    """Helper to create a notification."""
    return Notification.objects.create(
        organization=organization,
        user=user,
        notif_type=notif_type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action_url=action_url,
    )

"""Audit services."""
from .models import AuditLog


def log_action(user, organization, action, entity_type, entity_id, entity_label="", changes=None, request=None):
    """Helper to create an audit log entry from anywhere."""
    AuditLog.objects.create(
        user=user,
        organization=organization,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        entity_label=entity_label,
        changes=changes or {},
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
    )

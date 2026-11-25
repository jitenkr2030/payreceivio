"""Audit middleware - log every write action."""
import json

from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Only log mutating requests
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.user.is_authenticated:
            try:
                AuditLog.objects.create(
                    user=request.user,
                    organization=getattr(request, "active_organization", None),
                    action=self._action_for(request.method),
                    entity_type=self._entity_type_from_path(request.path),
                    entity_id="",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    metadata={"path": request.path, "method": request.method},
                )
            except Exception:
                pass  # never break the request because of audit logging
        return response

    def _action_for(self, method):
        return {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}.get(method, "view")

    def _entity_type_from_path(self, path):
        parts = path.strip("/").split("/")
        return parts[1] if len(parts) > 1 else parts[0] if parts else "unknown"

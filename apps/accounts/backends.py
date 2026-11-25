"""Backends and helpers for authentication."""
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import User


class EmailBackend(ModelBackend):
    """Authenticate by email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email")
        if not username or not password:
            return None
        try:
            user = User.objects.get(Q(email__iexact=username))
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

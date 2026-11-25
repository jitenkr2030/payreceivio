"""Zoho Books connector app."""
from django.apps import AppConfig


class ZohoConnectorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.zoho_connector"
    label = "zoho_connector"
    verbose_name = "Zoho Books Connector"

    def ready(self):
        from . import connector  # noqa

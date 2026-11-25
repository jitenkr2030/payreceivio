"""TallyPrime connector app."""
from django.apps import AppConfig


class TallyConnectorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tally_connector"
    label = "tally_connector"
    verbose_name = "TallyPrime Connector"

    def ready(self):
        # Import connector to trigger registration
        from . import connector  # noqa

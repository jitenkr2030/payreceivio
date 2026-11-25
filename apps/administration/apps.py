"""Administration app - org config, API tokens, data export."""
from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.administration"
    label = "administration"
    verbose_name = "Administration"

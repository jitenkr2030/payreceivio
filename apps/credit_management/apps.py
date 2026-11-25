"""Credit management app."""
from django.apps import AppConfig


class CreditManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.credit_management"
    label = "credit_management"
    verbose_name = "Credit Management"

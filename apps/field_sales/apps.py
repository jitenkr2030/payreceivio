"""Field sales app - salesperson portal."""
from django.apps import AppConfig


class FieldSalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.field_sales"
    label = "field_sales"
    verbose_name = "Field Sales"

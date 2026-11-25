"""AppConfig for accounting_connectors. Auto-registers all connectors."""
from django.apps import AppConfig


class AccountingConnectorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounting_connectors"
    label = "accounting_connectors"
    verbose_name = "Accounting Connectors"

    def ready(self):
        # Importing each connector module triggers @register_connector
        from .connectors import (  # noqa: F401
            busy, marg, quickbooks, xero, sage, dynamics365,
            netsuite, sap_b1, odoo, myob, freshbooks, wave,
            gofrugal, focus, exact, autocount, money_forward,
        )

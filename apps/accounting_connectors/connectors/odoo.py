"""
Odoo connector via XML-RPC and JSON-RPC.

Odoo is an open-source ERP. Authentication via database + API key (Odoo 14+).
Docs: https://www.odoo.com/documentation/16.0/developer/howtos/external_api.html
"""
import logging
import xmlrpc.client
from typing import List, Dict, Any

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.odoo")


@register_connector
class OdooConnector(BaseConnector):
    name = "odoo"
    label = "Odoo"
    vendor = "Odoo S.A."
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    def _url(self, connection, kind: str) -> str:
        host = connection.config.get("host", "").rstrip("/")
        return f"{host}/{kind}"

    def _auth(self, connection) -> tuple:
        """Common authentication - returns (uid, db, password, base_url)."""
        db = connection.config.get("database", "")
        username = connection.credentials.get("username", "")
        api_key = connection.credentials.get("api_key", "")
        common = xmlrpc.client.ServerProxy(f"{self._url(connection, 'xmlrpc/2')}/common")
        uid = common.authenticate(db, username, api_key, {})
        if not uid:
            raise ValueError("Odoo authentication failed")
        return uid, db, api_key

    def _models_proxy(self, connection):
        return xmlrpc.client.ServerProxy(f"{self._url(connection, 'xmlrpc/2')}/object")

    def authenticate(self, connection) -> bool:
        try:
            self._auth(connection)
            return True
        except Exception as e:
            log.error(f"Odoo auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        return self.authenticate(connection)

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        uid, db, api_key = self._auth(connection)
        models = self._models_proxy(connection)
        domain = [("customer_rank", ">", 0)]
        if since:
            domain.append(("write_date", ">=", since.isoformat()))
        ids = models.execute_kw(db, uid, api_key, "res.partner", "search",
                                [domain, {"limit": 1000}])
        return models.execute_kw(db, uid, api_key, "res.partner", "read",
                                [ids, ["id", "name", "email", "phone", "vat", "credit_limit"]])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        uid, db, api_key = self._auth(connection)
        models = self._models_proxy(connection)
        domain = [("move_type", "=", "out_invoice"), ("state", "=", "posted"),
                  ("payment_state", "in", ["not_paid", "partial"])]
        if since:
            domain.append(("write_date", ">=", since.isoformat()))
        ids = models.execute_kw(db, uid, api_key, "account.move", "search", [domain])
        return models.execute_kw(db, uid, api_key, "account.move", "read",
                                [ids, ["id", "name", "partner_id", "invoice_date", "invoice_date_due",
                                        "amount_total", "amount_residual", "state", "payment_state"]])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        uid, db, api_key = self._auth(connection)
        models = self._models_proxy(connection)
        domain = [("move_type", "=", "entry"), ("payment_state", "=", "paid")]
        if since:
            domain.append(("write_date", ">=", since.isoformat()))
        ids = models.execute_kw(db, uid, api_key, "account.payment", "search", [domain])
        return models.execute_kw(db, uid, api_key, "account.payment", "read",
                                [ids, ["id", "name", "partner_id", "amount", "date", "payment_method_line_id"]])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        uid, db, api_key = self._auth(connection)
        models = self._models_proxy(connection)
        # Create payment via account.payment model
        partner_id = payment.customer.metadata.get("odoo_id")
        if not partner_id:
            return {"success": False, "error": "Customer has no Odoo ID"}
        payment_vals = {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": partner_id,
            "amount": float(payment.amount),
            "date": payment.payment_date.isoformat(),
            "ref": payment.reference or payment.payment_number,
            "journal_id": connection.config.get("journal_id", 1),
            "payment_method_line_id": self._map_method(connection, payment.payment_method),
        }
        payment_id = models.execute_kw(db, uid, api_key, "account.payment", "create", [payment_vals])
        # Post the payment
        models.execute_kw(db, uid, api_key, "account.payment", "action_post", [payment_id])
        # Link to invoices
        for alloc in payment.allocations.all():
            inv_odoo_id = alloc.invoice.metadata.get("odoo_id")
            if inv_odoo_id:
                models.execute_kw(db, uid, api_key, "account.payment", "js_assign_outstanding_line",
                                  [payment_id, inv_odoo_id])
        return {"success": True, "ref": str(payment_id)}

    def _map_method(self, connection, method: str) -> int:
        # Payment method line IDs are tenant-specific. Caller must configure defaults.
        return connection.config.get("default_payment_method_line_id", 1)

"""
AutoCount connector.

AutoCount is a Malaysian/Southeast-Asian accounting software. Integration via:
1. AutoCount Task Server (REST API)
2. SQL Server direct access
3. .NET SDK / web service
"""
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.autocount")


@register_connector
class AutoCountConnector(BaseConnector):
    name = "autocount"
    label = "AutoCount"
    vendor = "AutoCount Sdn Bhd"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    def _base_url(self, connection) -> str:
        host = connection.config.get("host", "localhost")
        port = connection.config.get("port", 8081)
        return f"http://{host}:{port}/autocount/api/"

    def _headers(self, connection) -> dict:
        return {
            "X-AC-API-Key": connection.credentials.get("api_key", ""),
            "X-AC-Database": connection.config.get("database_name", ""),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._base_url(connection), "auth/verify"),
                                headers=self._headers(connection), timeout=15)
            return resp.status_code == 200
        except Exception as e:
            log.error(f"AutoCount auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        return self.authenticate(connection)

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {}
        if since:
            params["modified_after"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "masters/agents"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("agents", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"status": "open"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "transactions/ar-invoices"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("invoices", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._base_url(connection), "transactions/receipts"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("receipts", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "receipt_date": payment.payment_date.isoformat(),
            "debtor_code": payment.customer.code,
            "amount": float(payment.amount),
            "payment_method": self._map_method(payment.payment_method),
            "reference_no": payment.reference,
            "description": payment.notes or "",
            "invoice_allocations": [
                {"invoice_no": a.invoice.invoice_number, "amount": float(a.amount)}
                for a in payment.allocations.all()
            ],
        }
        resp = requests.post(urljoin(self._base_url(connection), "transactions/receipts"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("receipt_no", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        return {"upi": "UPI", "neft": "BANK", "rtgs": "BANK", "imps": "BANK",
                "cheque": "CHEQUE", "cash": "CASH", "card": "CARD"}.get(method, "OTHER")

"""
Marg ERP connector.

Marg ERP by Marg Compusolutions is widely used in the Indian pharma,
distribution, and retail segments. Integration options:
1. Marg API Server (add-on module)
2. MS-Access/SQL database direct access
3. CSV/Excel import-export

This connector uses the Marg API Server (default port 8999) when available.
"""
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.marg")


@register_connector
class MargConnector(BaseConnector):
    name = "marg"
    label = "Marg ERP"
    vendor = "Marg Compusolutions"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    def _base_url(self, connection) -> str:
        return connection.config.get("api_url", "http://localhost:8999").rstrip("/") + "/api/"

    def _headers(self, connection) -> dict:
        return {
            "X-Marg-API-Key": connection.credentials.get("api_key", ""),
            "X-Marg-Company": connection.config.get("company_code", ""),
            "Content-Type": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._base_url(connection), "auth/check"),
                                headers=self._headers(connection), timeout=15)
            return resp.status_code == 200
        except Exception as e:
            log.error(f"Marg auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        return self.authenticate(connection)

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"modified_after": since.isoformat()} if since else {}
        resp = requests.get(urljoin(self._base_url(connection), "masters/parties"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("parties", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"type": "sale", "pending": "true"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "transactions/sale"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("invoices", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"type": "receipt"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "transactions/receipt"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("receipts", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "voucher_date": payment.payment_date.isoformat(),
            "party_code": payment.customer.code,
            "amount": float(payment.amount),
            "mode": self._map_mode(payment.payment_method),
            "reference_no": payment.reference,
            "narration": payment.notes or "",
            "bill_adjustments": [
                {"bill_no": a.invoice.invoice_number, "amount": float(a.amount)}
                for a in payment.allocations.all()
            ],
        }
        resp = requests.post(urljoin(self._base_url(connection), "transactions/receipt"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("voucher_no", "")}
        return {"success": False, "error": resp.text}

    def _map_mode(self, method: str) -> str:
        return {"upi": "UPI", "neft": "Bank", "rtgs": "Bank", "imps": "Bank",
                "cheque": "Cheque", "cash": "Cash"}.get(method, "Other")

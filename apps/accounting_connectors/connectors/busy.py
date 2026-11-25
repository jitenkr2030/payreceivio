"""
BUSY ERP connector.

BUSY is a popular Indian SMB accounting software by BUSY Infotech.
Integration options:
1. BUSY REST API (BUSY 21+ with API add-on)
2. Excel/CSV export-import
3. Direct database access (BUSY uses SQL Server Express / LocalDB)

This connector uses the official BUSY REST API when available, with
file-based import/export as fallback.
"""
import logging
from datetime import date
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.busy")


@register_connector
class BusyConnector(BaseConnector):
    name = "busy"
    label = "BUSY"
    vendor = "BUSY Infotech"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]
    BASE_PATH = "/api/v1/"

    def _base_url(self, connection) -> str:
        return connection.config.get("api_url", "http://localhost:5400").rstrip("/") + self.BASE_PATH

    def _headers(self, connection) -> dict:
        return {
            "Authorization": f"Bearer {connection.credentials.get('api_token', '')}",
            "Content-Type": "application/json",
            "X-Busy-Company": connection.config.get("company_code", ""),
        }

    def authenticate(self, connection) -> bool:
        try:
            resp = requests.get(
                urljoin(self._base_url(connection), "auth/verify"),
                headers=self._headers(connection), timeout=15,
            )
            return resp.status_code == 200
        except Exception as e:
            log.error(f"BUSY auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        return self.authenticate(connection)

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"group": "Sundry Debtors"}
        if since:
            params["modified_since"] = since.isoformat()
        resp = requests.get(
            urljoin(self._base_url(connection), "masters/accounts"),
            headers=self._headers(connection), params=params, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"type": "sales", "status": "unpaid"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(
            urljoin(self._base_url(connection), "transactions/vouchers"),
            headers=self._headers(connection), params=params, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"type": "receipt"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(
            urljoin(self._base_url(connection), "transactions/vouchers"),
            headers=self._headers(connection), params=params, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "voucher_type": "Receipt",
            "voucher_date": payment.payment_date.isoformat(),
            "voucher_number": payment.receipt_number or payment.payment_number,
            "account": payment.customer.name,
            "amount": float(payment.amount),
            "narration": payment.notes or f"Receipt via PayReceivio {payment.payment_number}",
            "mode": self._map_mode(payment.payment_method),
            "reference": payment.reference,
            "bill_allocations": [
                {"bill_no": a.invoice.invoice_number, "amount": float(a.amount)}
                for a in payment.allocations.all()
            ],
        }
        resp = requests.post(
            urljoin(self._base_url(connection), "transactions/vouchers"),
            headers=self._headers(connection), json=payload, timeout=30,
        )
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("voucher_number", "")}
        return {"success": False, "error": resp.text}

    def _map_mode(self, method: str) -> str:
        return {"upi": "UPI", "neft": "Bank", "rtgs": "Bank", "imps": "Bank",
                "cheque": "Cheque", "cash": "Cash", "card": "Card"}.get(method, "Other")

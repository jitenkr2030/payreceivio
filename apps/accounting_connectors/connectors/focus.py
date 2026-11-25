"""
Focus Softnet (Focus 9 / Focus i) connector.

Focus Softnet is a UAE/India-based ERP vendor. Integration via:
1. Focus iConnect REST API
2. SQL Server direct access
3. File-based import-export

This connector uses the iConnect REST API.
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.focus")


@register_connector
class FocusSoftnetConnector(BaseConnector):
    name = "focus"
    label = "Focus Softnet (Focus 9/i)"
    vendor = "Focus Softnet"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    def _base_url(self, connection) -> str:
        host = connection.config.get("host", "localhost")
        port = connection.config.get("port", 8080)
        return f"http://{host}:{port}/iconnect/api/v1/"

    def _refresh_token(self, connection) -> str:
        """Focus iConnect uses JWT with refresh."""
        refresh_token = connection.credentials.get("refresh_token")
        if not refresh_token:
            raise ValueError("Missing Focus refresh token")
        resp = requests.post(urljoin(self._base_url(connection), "auth/refresh"),
            json={"refresh_token": refresh_token}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        connection.credentials["access_token"] = data["access_token"]
        connection.credentials["expires_at"] = str(time.time() + data.get("expires_in", 3600))
        connection.save()
        return data["access_token"]

    def _access_token(self, connection) -> str:
        token = connection.credentials.get("access_token")
        expires = connection.credentials.get("expires_at")
        if not token or (expires and float(expires) < time.time() + 60):
            return self._refresh_token(connection)
        return token

    def _headers(self, connection) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token(connection)}",
            "X-Company-Code": connection.config.get("company_code", ""),
            "Content-Type": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"Focus auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._base_url(connection), "company/info"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {}
        if since:
            params["modified_after"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "masters/accounts"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("accounts", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"voucher_type": "sales", "status": "open"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "transactions/vouchers"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("vouchers", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"voucher_type": "receipt"}
        if since:
            params["from_date"] = since.isoformat()
        resp = requests.get(urljoin(self._base_url(connection), "transactions/vouchers"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("vouchers", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "voucher_type": "receipt",
            "voucher_date": payment.payment_date.isoformat(),
            "account_code": payment.customer.code,
            "amount": float(payment.amount),
            "mode": self._map_mode(payment.payment_method),
            "reference_no": payment.reference,
            "narration": payment.notes or "",
            "bill_allocations": [
                {"bill_no": a.invoice.invoice_number, "amount": float(a.amount)}
                for a in payment.allocations.all()
            ],
        }
        resp = requests.post(urljoin(self._base_url(connection), "transactions/vouchers"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("voucher_no", "")}
        return {"success": False, "error": resp.text}

    def _map_mode(self, method: str) -> str:
        return {"upi": "UPI", "neft": "BANK", "rtgs": "BANK", "imps": "BANK",
                "cheque": "CHEQUE", "cash": "CASH"}.get(method, "OTHER")

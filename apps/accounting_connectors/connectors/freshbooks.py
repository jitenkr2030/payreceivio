"""
FreshBooks connector.

OAuth 2.0 + FreshBooks REST API.
Docs: https://www.freshbooks.com/api/start
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.freshbooks")


@register_connector
class FreshBooksConnector(BaseConnector):
    name = "freshbooks"
    label = "FreshBooks"
    vendor = "FreshBooks"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    API_BASE = "https://api.freshbooks.com/"
    AUTH_URL = "https://api.freshbooks.com/auth/oauth/token"

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing FreshBooks OAuth credentials")
        resp = requests.post(self.AUTH_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        connection.credentials["access_token"] = data["access_token"]
        connection.credentials["refresh_token"] = data.get("refresh_token", refresh_token)
        connection.credentials["expires_at"] = str(time.time() + data.get("expires_in", 43200))
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
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _account_id(self, connection) -> str:
        return connection.config.get("account_id", "")

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"FreshBooks auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self.API_BASE, "auth/api/v1/users/me"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        url = urljoin(self.API_BASE, f"accounting/account/{self._account_id(connection)}/users/clients")
        resp = requests.get(url, headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("response", {}).get("clients", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        url = urljoin(self.API_BASE, f"accounting/account/{self._account_id(connection)}/invoices/invoices")
        params = {"search[status]": "unpaid"}
        if since:
            params["search[updated_since]"] = since.isoformat()
        resp = requests.get(url, headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("response", {}).get("invoices", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        url = urljoin(self.API_BASE, f"accounting/account/{self._account_id(connection)}/payments/payments")
        resp = requests.get(url, headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("response", {}).get("payments", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        url = urljoin(self.API_BASE, f"accounting/account/{self._account_id(connection)}/payments/payments")
        payload = {
            "payment": {
                "clientid": payment.customer.metadata.get("freshbooks_id", ""),
                "amount": {"amount": str(payment.amount), "code": payment.currency},
                "date": payment.payment_date.isoformat(),
                "type": self._map_type(payment.payment_method),
                "note": payment.notes or f"PayReceivio {payment.payment_number}",
            }
        }
        resp = requests.post(url, headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("response", {}).get("payment", {}).get("id", "")}
        return {"success": False, "error": resp.text}

    def _map_type(self, method: str) -> str:
        return {"upi": "Upi", "neft": "Bank", "rtgs": "Bank", "imps": "Bank",
                "cheque": "Check", "cash": "Cash", "card": "Credit"}.get(method, "Other")

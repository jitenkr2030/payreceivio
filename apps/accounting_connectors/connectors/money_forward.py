"""
Money Forward Cloud Accounting connector (Japan).

OAuth 2.0 + Money Forward Cloud API.
Docs: https://developer.moneyforward.com/
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.money_forward")


@register_connector
class MoneyForwardConnector(BaseConnector):
    name = "money_forward"
    label = "Money Forward Cloud"
    vendor = "Money Forward"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    API_BASE = "https://api.moneyforward.com/api/v1/"
    AUTH_URL = "https://api.moneyforward.com/oauth/token"

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing Money Forward OAuth credentials")
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
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _office_id(self, connection) -> str:
        return connection.config.get("office_id", "")

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"Money Forward auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self.API_BASE, "user.json"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        url = urljoin(self.API_BASE, f"offices/{self._office_id(connection)}/partners.json")
        resp = requests.get(url, headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("partners", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        url = urljoin(self.API_BASE, f"offices/{self._office_id(connection)}/deals.json")
        params = {"status": "open"}
        if since:
            params["updated_since"] = since.isoformat()
        resp = requests.get(url, headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("deals", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        url = urljoin(self.API_BASE, f"offices/{self._office_id(connection)}/payments.json")
        resp = requests.get(url, headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("payments", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        url = urljoin(self.API_BASE, f"offices/{self._office_id(connection)}/payments.json")
        payload = {
            "payment": {
                "partner_id": payment.customer.metadata.get("mf_id", ""),
                "date": payment.payment_date.isoformat(),
                "amount": float(payment.amount),
                "method": self._map_method(payment.payment_method),
                "reference": payment.reference or payment.payment_number,
                "note": payment.notes or "",
            }
        }
        resp = requests.post(url, headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("payment", {}).get("id", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        return {"upi": "upi", "neft": "bank_transfer", "rtgs": "bank_transfer",
                "imps": "bank_transfer", "cheque": "cheque", "cash": "cash",
                "card": "credit_card"}.get(method, "other")

"""
Oracle NetSuite connector.

OAuth 2.0 / TBA (Token-Based Authentication) + SuiteTalk REST API.
Docs: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159104345424.html
"""
import logging
import time
import base64
import hmac
import hashlib
import urllib.parse
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.netsuite")


@register_connector
class NetSuiteConnector(BaseConnector):
    name = "netsuite"
    label = "Oracle NetSuite"
    vendor = "Oracle"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    def _base_url(self, connection) -> str:
        account = connection.config.get("account_id", "").replace("-", "_")
        return f"https://{account}.suitetalk.api.netsuite.com/services/rest/record/v1/"

    def _refresh_token(self, connection) -> str:
        # NetSuite OAuth 2.0 server-to-server flow
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing NetSuite OAuth credentials")
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post(
            "https://system.netsuite.com/apps/oauth2/v1/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )
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
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "transient",
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"NetSuite auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._base_url(connection), "customer"),
                                headers=self._headers(connection),
                                params={"limit": 1}, timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"limit": 1000}
        if since:
            params["q"] = f'lastModifiedDate ON_OR_AFTER "{since.isoformat()}"'
        resp = requests.get(urljoin(self._base_url(connection), "customer"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("items", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        # Filter for open invoices via suiteQL
        params = {"limit": 1000}
        resp = requests.get(urljoin(self._base_url(connection), "invoice"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        # Filter open invoices
        return [i for i in items if i.get("status") in ("Open", "_open")]

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._base_url(connection), "customerPayment"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("items", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "entity": {"id": payment.customer.metadata.get("ns_id", "")},
            "externalId": payment.payment_number,
            "tranDate": payment.payment_date.isoformat(),
            "paymentMethod": self._map_method(payment.payment_method),
            "memo": payment.notes or "",
            "undepFunds": False,
            "applied": [
                {"doc": a.invoice.metadata.get("ns_id", ""), "amount": float(a.amount)}
                for a in payment.allocations.all()
            ],
        }
        resp = requests.post(urljoin(self._base_url(connection), "customerPayment"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("id", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        # NetSuite internal IDs for payment methods
        return {"upi": "_upi", "neft": "_neft", "rtgs": "_rtgs", "imps": "_imps",
                "cheque": "_check", "cash": "_cash", "card": "_creditCard"}.get(method, "_other")

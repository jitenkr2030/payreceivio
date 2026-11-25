"""
Sage Business Cloud Accounting connector.

OAuth 2.0 + Sage Accounting REST API v3.
Docs: https://developer.sage.com/accounting/reference/
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.sage")


@register_connector
class SageConnector(BaseConnector):
    name = "sage"
    label = "Sage Business Cloud"
    vendor = "Sage Group"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    BASE_URLS = {
        "eu": "https://api.accounting.sage.com/v3.1/",
        "us": "https://api.accounting.sage.com/v3.1/",
        "ca": "https://api.cdnaccounting.sage.com/v3.1/",
        "uk": "https://api.accounting.sage.com/v3.1/",
    }
    AUTH_URL = "https://oauth.accounting.sage.com/oauth2/token/"

    def _base_url(self, connection) -> str:
        region = connection.config.get("region", "eu")
        return self.BASE_URLS.get(region, self.BASE_URLS["eu"])

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing Sage OAuth credentials")
        resp = requests.post(
            self.AUTH_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30,
        )
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
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Sage-Region": connection.config.get("region", "eu"),
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"Sage auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._base_url(connection), "contact_statuses"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"contact_type": "CUSTOMER", "is_active": "true"}
        if since:
            params["updated_or_created_since"] = since.isoformat() + "Z"
        resp = requests.get(urljoin(self._base_url(connection), "contacts"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("$items", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"status": "OPEN", "search": "sales_invoices"}
        if since:
            params["updated_or_created_since"] = since.isoformat() + "Z"
        resp = requests.get(urljoin(self._base_url(connection), "sales_invoices"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("$items", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._base_url(connection), "sales_payments"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("$items", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "sales_payment": {
                "transaction_type_id": "CUSTOMER_RECEIPT",
                "contact_id": payment.customer.metadata.get("sage_id", ""),
                "date": payment.payment_date.isoformat(),
                "total_amount": float(payment.amount),
                "reference": payment.reference or payment.payment_number,
                "payment_method_id": self._map_method_id(connection, payment.payment_method),
                "artefacts": [
                    {"artefact_id": a.invoice.metadata.get("sage_id", ""),
                     "amount": float(a.amount)} for a in payment.allocations.all()
                ],
            }
        }
        resp = requests.post(urljoin(self._base_url(connection), "sales_payments"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("id", "")}
        return {"success": False, "error": resp.text}

    def _map_method_id(self, connection, method: str) -> str:
        # Lookup the Sage payment method ID for a given PayReceivio method
        # Real impl would query /payment_methods and cache the mapping
        return connection.config.get("default_payment_method_id", "")

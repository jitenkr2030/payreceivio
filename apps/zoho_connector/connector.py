"""
Zoho Books connector via REST API and OAuth 2.0.

API docs: https://www.zoho.com/books/api/v3/
OAuth flow: authorization code grant with refresh token.
"""
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests
from django.conf import settings

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.zoho")


@register_connector
class ZohoConnector(BaseConnector):
    name = "zoho"
    label = "Zoho Books"
    vendor = "Zoho"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    BASE_URLS = {
        "com": "https://www.zohoapis.com/books/v3/",
        "in": "https://www.zohoapis.in/books/v3/",
        "eu": "https://www.zohoapis.eu/books/v3/",
        "us": "https://www.zohoapis.com/books/v3/",
    }
    AUTH_URLS = {
        "com": "https://accounts.zoho.com/oauth/v2/",
        "in": "https://accounts.zoho.in/oauth/v2/",
        "eu": "https://accounts.zoho.eu/oauth/v2/",
    }

    def _data_center(self, connection) -> str:
        return connection.config.get("data_center", settings.PAYRECEIVIO.get("ZOHO_DATA_CENTER", "in"))

    def _base_url(self, connection) -> str:
        dc = self._data_center(connection)
        return self.BASE_URLS.get(dc, self.BASE_URLS["com"])

    def _refresh_access_token(self, connection) -> str:
        """Use the refresh token to get a new access token."""
        dc = self._data_center(connection)
        auth_url = self.AUTH_URLS.get(dc, self.AUTH_URLS["com"])
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing OAuth credentials")
        resp = requests.post(urljoin(auth_url, "token"), data={
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        connection.credentials["access_token"] = data["access_token"]
        connection.credentials["expires_at"] = str(__import__("time").time() + data.get("expires_in", 3600))
        connection.save()
        return data["access_token"]

    def _get_access_token(self, connection) -> str:
        import time
        token = connection.credentials.get("access_token")
        expires = connection.credentials.get("expires_at")
        if not token or (expires and float(expires) < time.time() + 60):
            return self._refresh_access_token(connection)
        return token

    def _headers(self, connection) -> dict:
        return {
            "Authorization": f"Zoho-oauthtoken {self._get_access_token(connection)}",
            "Content-Type": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            self._get_access_token(connection)
            return True
        except Exception as e:
            log.error(f"Zoho auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            org_id = connection.config.get("organization_id")
            resp = requests.get(
                urljoin(self._base_url(connection), "organizations"),
                headers=self._headers(connection),
                params={"organization_id": org_id},
                timeout=30,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        org_id = connection.config.get("organization_id")
        resp = requests.get(
            urljoin(self._base_url(connection), "contacts"),
            headers=self._headers(connection),
            params={"organization_id": org_id, "contact_type": "customer"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("contacts", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        org_id = connection.config.get("organization_id")
        params = {"organization_id": org_id, "status": "unpaid"}
        if since:
            params["last_modified_date"] = since.isoformat()
        resp = requests.get(
            urljoin(self._base_url(connection), "invoices"),
            headers=self._headers(connection), params=params, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("invoices", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        org_id = connection.config.get("organization_id")
        resp = requests.get(
            urljoin(self._base_url(connection), "customerpayments"),
            headers=self._headers(connection),
            params={"organization_id": org_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("customer_payments", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        org_id = connection.config.get("organization_id")
        payload = {
            "customer_id": payment.customer.metadata.get("zoho_id", ""),
            "payment_mode": self._map_payment_mode(payment.payment_method),
            "amount": str(payment.amount),
            "date": payment.payment_date.isoformat(),
            "reference_number": payment.reference,
            "description": payment.notes or f"Receipt via PayReceivio {payment.payment_number}",
            "invoices": [{"invoice_id": a.invoice.metadata.get("zoho_id", ""),
                          "amount_applied": str(a.amount)} for a in payment.allocations.all()],
        }
        resp = requests.post(
            urljoin(self._base_url(connection), "customerpayments"),
            headers=self._headers(connection),
            params={"organization_id": org_id},
            json=payload, timeout=30,
        )
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("payment", {}).get("payment_id", "")}
        return {"success": False, "error": resp.text}

    def _map_payment_mode(self, method: str) -> str:
        return {
            "upi": "upi", "neft": "nettransfer", "rtgs": "nettransfer",
            "imps": "nettransfer", "cheque": "check", "cash": "cash",
            "card": "creditcard", "net_banking": "nettransfer",
        }.get(method, "other")

"""
Exact Online connector.

OAuth 2.0 + Exact Online REST API.
Docs: https://start.exactonline.nl/docs/HlpRestAPIIndex.aspx
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.exact")


@register_connector
class ExactOnlineConnector(BaseConnector):
    name = "exact"
    label = "Exact Online"
    vendor = "Exact"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    BASE_URLS = {
        "nl": "https://start.exactonline.nl/api/v1/",
        "be": "https://start.exactonline.be/api/v1/",
        "de": "https://start.exactonline.de/api/v1/",
        "uk": "https://start.exactonline.co.uk/api/v1/",
        "us": "https://start.exactonline.us/api/v1/",
    }
    AUTH_URLS = {
        "nl": "https://start.exactonline.nl/api/oauth2/token",
        "be": "https://start.exactonline.be/api/oauth2/token",
        "de": "https://start.exactonline.de/api/oauth2/token",
        "uk": "https://start.exactonline.co.uk/api/oauth2/token",
        "us": "https://start.exactonline.us/api/oauth2/token",
    }

    def _base_url(self, connection) -> str:
        region = connection.config.get("region", "nl")
        return self.BASE_URLS.get(region, self.BASE_URLS["nl"])

    def _auth_url(self, connection) -> str:
        region = connection.config.get("region", "nl")
        return self.AUTH_URLS.get(region, self.AUTH_URLS["nl"])

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing Exact Online OAuth credentials")
        resp = requests.post(self._auth_url(connection), data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        connection.credentials["access_token"] = data["access_token"]
        connection.credentials["refresh_token"] = data.get("refresh_token", refresh_token)
        connection.credentials["expires_at"] = str(time.time() + data.get("expires_in", 600))
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
        }

    def _division(self, connection) -> str:
        return connection.config.get("division", "1")

    def _url(self, connection, endpoint: str) -> str:
        return urljoin(self._base_url(connection), f"{self._division(connection)}/{endpoint}")

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"Exact auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(self._url(connection, "system/Me"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(self._url(connection, "crm/Accounts"),
                            headers=self._headers(connection),
                            params={"$filter": "IsCustomer eq true", "$top": 1000},
                            timeout=30)
        resp.raise_for_status()
        return resp.json().get("d", {}).get("results", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"$filter": "AmountDC gt 0", "$top": 1000}
        if since:
            params["$filter"] += f" and Modified gt datetime'{since.isoformat()}'"
        resp = requests.get(self._url(connection, "salesinvoice/SalesInvoices"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("d", {}).get("results", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(self._url(connection, "financialtransaction/SyncFinancialTransactions"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("d", {}).get("results", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "Account": payment.customer.metadata.get("exact_id", ""),
            "Date": payment.payment_date.isoformat(),
            "AmountDC": float(payment.amount),
            "PaymentMethod": self._map_method(payment.payment_method),
            "Reference": payment.reference or payment.payment_number,
            "Description": payment.notes or "",
        }
        resp = requests.post(self._url(connection, "cashflow/Receivables"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("d", {}).get("EntryID", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        return {"upi": "UPI", "neft": "BANK", "rtgs": "BANK", "imps": "BANK",
                "cheque": "CHEQUE", "cash": "CASH", "card": "CARD"}.get(method, "OTHER")

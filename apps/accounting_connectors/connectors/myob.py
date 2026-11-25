"""
MYOB (AccRight / AccountRight) connector.

OAuth 2.0 + MYOB AccountRight REST API.
Docs: https://developer.myob.com/api/accountright/api-overview
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests
from django.conf import settings

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.myob")


@register_connector
class MYOBConnector(BaseConnector):
    name = "myob"
    label = "MYOB AccountRight"
    vendor = "MYOB"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    API_BASE = "https://api.myob.com/accountright/"
    AUTH_URL = "https://secure.myob.com/oauth2/v1/authorize"
    TOKEN_URL = "https://secure.myob.com/oauth2/v1/token"

    def _company_url(self, connection) -> str:
        company_file = connection.config.get("company_file_uid", "")
        return urljoin(self.API_BASE, f"{company_file}/")

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing MYOB OAuth credentials")
        resp = requests.post(self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        connection.credentials["access_token"] = data["access_token"]
        connection.credentials["refresh_token"] = data.get("refresh_token", refresh_token)
        connection.credentials["expires_at"] = str(time.time() + data.get("expires_in", 1200))
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
            "x-myobapi-key": connection.credentials.get("client_id", ""),
            "x-myobapi-version": "v2",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"MYOB auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._company_url(connection), "Company"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._company_url(connection), "Contact/Customer"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("Items", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"$filter": "Status eq 'Open'"}
        resp = requests.get(urljoin(self._company_url(connection), "Sale/Invoice"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("Items", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._company_url(connection), "Sale/CustomerPayment"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("Items", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "Customer": {"UID": payment.customer.metadata.get("myob_uid", "")},
            "DateReceived": payment.payment_date.isoformat(),
            "AmountReceived": float(payment.amount),
            "PaymentMethod": self._map_method(payment.payment_method),
            "Reference": payment.reference or payment.payment_number,
            "Memo": payment.notes or "",
            "Invoices": [
                {"UID": a.invoice.metadata.get("myob_uid", ""), "AmountApplied": float(a.amount)}
                for a in payment.allocations.all()
            ],
            "Account": {"UID": connection.config.get("deposit_account_uid", "")},
        }
        resp = requests.post(urljoin(self._company_url(connection), "Sale/CustomerPayment"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("UID", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        return {"upi": "Upi", "neft": "Bank", "rtgs": "Bank", "imps": "Bank",
                "cheque": "Cheque", "cash": "Cash", "card": "CreditCard"}.get(method, "Other")

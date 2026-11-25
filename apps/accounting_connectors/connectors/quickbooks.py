"""
QuickBooks Online connector (Intuit).

OAuth 2.0 + QuickBooks V3 REST API.
Docs: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests
from django.conf import settings

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.quickbooks")


@register_connector
class QuickBooksConnector(BaseConnector):
    name = "quickbooks"
    label = "QuickBooks Online"
    vendor = "Intuit"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    PRODUCTION_BASE = "https://quickbooks.api.intuit.com/v3/company/"
    SANDBOX_BASE = "https://sandbox-quickbooks.api.intuit.com/v3/company/"
    AUTH_URL = "https://oauth.platform.intuit.com/oauth2/v1/"
    DISCOVERY_URL = "https://developer.intuit.com/.well-known/openid_sandbox_configuration/"

    def _base_url(self, connection) -> str:
        realm = connection.config.get("realm_id", "")
        env = connection.config.get("environment", "production")
        base = self.PRODUCTION_BASE if env == "production" else self.SANDBOX_BASE
        return base + realm + "/"

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing QuickBooks OAuth credentials")
        resp = requests.post(
            urljoin(self.AUTH_URL, "tokens/bearer"),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(client_id, client_secret),
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
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"QuickBooks auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(
                urljoin(self._base_url(connection), "query"),
                headers=self._headers(connection),
                params={"query": "SELECT * FROM Customer MAXRESULTS 1"},
                timeout=30,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Customer WHERE Active = true"
        if since:
            query += f" AND Metadata.LastUpdatedTime > '{since.isoformat()}'"
        resp = requests.get(
            urljoin(self._base_url(connection), "query"),
            headers=self._headers(connection),
            params={"query": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("QueryResponse", {}).get("Customer", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Invoice WHERE Balance > 0"
        if since:
            query += f" AND Metadata.LastUpdatedTime > '{since.isoformat()}'"
        resp = requests.get(
            urljoin(self._base_url(connection), "query"),
            headers=self._headers(connection),
            params={"query": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("QueryResponse", {}).get("Invoice", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Payment"
        if since:
            query += f" WHERE Metadata.LastUpdatedTime > '{since.isoformat()}'"
        resp = requests.get(
            urljoin(self._base_url(connection), "query"),
            headers=self._headers(connection),
            params={"query": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("QueryResponse", {}).get("Payment", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "Payment": {
                "CustomerRef": {"value": payment.customer.metadata.get("qbo_id", "")},
                "TotalAmt": float(payment.amount),
                "TxnDate": payment.payment_date.isoformat(),
                "PaymentRefNum": payment.reference,
                "PaymentMethod": self._map_method(payment.payment_method),
                "PrivateNote": payment.notes or f"PayReceivio {payment.payment_number}",
                "Line": [
                    {
                        "Amount": float(a.amount),
                        "LinkedTxn": [{"TxnId": a.invoice.metadata.get("qbo_id", ""),
                                        "TxnType": "Invoice"}],
                    } for a in payment.allocations.all()
                ],
            }
        }
        resp = requests.post(
            urljoin(self._base_url(connection), "payment"),
            headers=self._headers(connection),
            json=payload,
            params={"minorversion": "65"},
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("Payment", {}).get("Id", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        return {"upi": "UPI", "neft": "Check", "rtgs": "Check", "imps": "Check",
                "cheque": "Check", "cash": "Cash", "card": "Credit Card"}.get(method, "Other")

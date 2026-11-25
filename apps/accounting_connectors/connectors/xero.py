"""
Xero connector.

OAuth 2.0 + Xero Accounting REST API.
Docs: https://developer.xero.com/documentation/api/accounting/overview
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.xero")


@register_connector
class XeroConnector(BaseConnector):
    name = "xero"
    label = "Xero"
    vendor = "Xero"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    API_BASE = "https://api.xero.com/api.xro/2.0/"
    AUTH_BASE = "https://identity.xero.com/connect/token"
    TENANT_URL = "https://api.xero.com/connections/"

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing Xero OAuth credentials")
        import base64
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post(
            self.AUTH_BASE,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        connection.credentials["access_token"] = data["access_token"]
        connection.credentials["refresh_token"] = data["refresh_token"]
        connection.credentials["expires_at"] = str(time.time() + data.get("expires_in", 1800))
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
            "Xero-tenant-id": connection.config.get("tenant_id", ""),
            "Accept": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"Xero auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self.API_BASE, "Organisations"),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {}
        if since:
            from datetime import datetime
            params["where"] = f'ContactStatus=="ACTIVE"&&ModifiedDate>DateTime({since.year},{since.month},{since.day})'
        resp = requests.get(urljoin(self.API_BASE, "Contacts"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("Contacts", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"where": 'Type=="ACCREC"&&AmountDue>0'}
        if since:
            from datetime import datetime
            params["where"] += f'&&ModifiedDate>DateTime({since.year},{since.month},{since.day})'
        resp = requests.get(urljoin(self.API_BASE, "Invoices"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("Invoices", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"where": 'Type=="ACCREC_PAYMENT"'}
        resp = requests.get(urljoin(self.API_BASE, "Payments"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("Payments", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "Payments": [{
                "Account": {"Code": connection.config.get("bank_account_code", "090")},
                "Date": payment.payment_date.isoformat(),
                "Reference": payment.reference or payment.payment_number,
                "Amount": float(payment.amount),
                "Invoice": {
                    "InvoiceID": payment.allocations.first().invoice.metadata.get("xero_id", "") if payment.allocations.first() else "",
                },
                "IsReconciled": False,
            }]
        }
        resp = requests.put(urljoin(self.API_BASE, "Payments"),
                            headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("Payments", [{}])[0].get("PaymentID", "")}
        return {"success": False, "error": resp.text}

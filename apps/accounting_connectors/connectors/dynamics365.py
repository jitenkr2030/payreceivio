"""
Microsoft Dynamics 365 Business Central connector.

OAuth 2.0 (Azure AD) + Business Central REST API v2.0.
Docs: https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.d365bc")


@register_connector
class Dynamics365Connector(BaseConnector):
    name = "dynamics365"
    label = "Microsoft Dynamics 365 Business Central"
    vendor = "Microsoft"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    API_BASE = "https://api.businesscentral.dynamics.com/v2.0/"
    AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    ENVIRONMENTS = {"production": "production", "sandbox": "sandbox"}

    def _base_url(self, connection) -> str:
        env = connection.config.get("environment", "production")
        company_id = connection.config.get("company_id", "")
        tenant = connection.config.get("tenant_id", "common")
        return f"{self.API_BASE}{env}/api/v2.0/companies({company_id})/"

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        tenant = connection.config.get("tenant_id", "common")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing D365 OAuth credentials")
        resp = requests.post(
            self.AUTH_URL.format(tant=tenant),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://api.businesscentral.dynamics.com/.default",
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
        }

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"D365 auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(self._base_url(connection),
                                headers=self._headers(connection), timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._base_url(connection), "customers"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        # OData filter for unpaid sales invoices
        params = {"$filter": "status eq 'Open'"}
        resp = requests.get(urljoin(self._base_url(connection), "salesInvoices"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._base_url(connection), "customerPaymentJournals"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        # Step 1: create customer payment
        payload = {
            "customerId": payment.customer.metadata.get("d365_id", ""),
            "postingDate": payment.payment_date.isoformat(),
            "amount": float(payment.amount),
            "externalDocumentNo": payment.reference or payment.payment_number,
            "paymentMethod": self._map_method(payment.payment_method),
            "description": payment.notes or f"PayReceivio {payment.payment_number}",
        }
        resp = requests.post(urljoin(self._base_url(connection), "customerPayments"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": resp.json().get("id", "")}
        return {"success": False, "error": resp.text}

    def _map_method(self, method: str) -> str:
        return {"upi": "UPI", "neft": "BANK", "rtgs": "BANK", "imps": "BANK",
                "cheque": "CHECK", "cash": "CASH", "card": "CARD"}.get(method, "OTHER")

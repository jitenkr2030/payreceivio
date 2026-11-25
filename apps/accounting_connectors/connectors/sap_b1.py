"""
SAP Business One connector via Service Layer.

SAP B1 Service Layer is a REST API exposed on port 50000 (HTTP) / 50001 (HTTPS).
Docs: https://help.sap.com/docs/SAP_BUSINESS_ONE/68a2e87fbf9442e8bc4f8e982b4f8c7d/d4c1f4a7c11e4430b2b62ce63f46d6da.html
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.sap_b1")


@register_connector
class SAPBusinessOneConnector(BaseConnector):
    name = "sap_b1"
    label = "SAP Business One"
    vendor = "SAP"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    def _base_url(self, connection) -> str:
        host = connection.config.get("host", "localhost")
        port = connection.config.get("port", 50000)
        company = connection.config.get("company_db", "")
        return f"http://{host}:{port}/b1s/v1/"

    def _login(self, connection) -> str:
        """Login to SAP B1 Service Layer and store session cookie."""
        payload = {
            "CompanyDB": connection.config.get("company_db", ""),
            "UserName": connection.credentials.get("username", ""),
            "Password": connection.credentials.get("password", ""),
        }
        session = requests.Session()
        resp = session.post(urljoin(self._base_url(connection), "Login"),
                            json=payload, timeout=30)
        resp.raise_for_status()
        # SAP B1 uses B1SESSION + ROUTEID cookies
        connection.credentials["session_cookie"] = resp.cookies.get("B1SESSION", "")
        connection.credentials["route_id"] = resp.cookies.get("ROUTEID", "")
        connection.credentials["session_expires"] = str(time.time() + 1800)  # 30 min
        connection.save()
        return connection.credentials["session_cookie"]

    def _session_cookie(self, connection) -> str:
        cookie = connection.credentials.get("session_cookie", "")
        expires = connection.credentials.get("session_expires", "0")
        if not cookie or float(expires) < time.time() + 60:
            return self._login(connection)
        return cookie

    def _headers(self, connection) -> dict:
        return {
            "Cookie": f"B1SESSION={self._session_cookie(connection)};ROUTEID={connection.credentials.get('route_id', '')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def authenticate(self, connection) -> bool:
        try:
            self._login(connection)
            return True
        except Exception as e:
            log.error(f"SAP B1 auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            resp = requests.get(urljoin(self._base_url(connection), "BusinessPartners"),
                                headers=self._headers(connection),
                                params={"$top": 1, "$filter": "CardType eq 'cCustomer'"},
                                timeout=30)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        params = {"$filter": "CardType eq 'cCustomer'", "$top": 1000}
        resp = requests.get(urljoin(self._base_url(connection), "BusinessPartners"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        # Open sales invoices with outstanding balance
        params = {"$filter": "DocumentStatus eq 'bost_Open'", "$top": 1000}
        resp = requests.get(urljoin(self._base_url(connection), "Invoices"),
                            headers=self._headers(connection), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        resp = requests.get(urljoin(self._base_url(connection), "IncomingPayments"),
                            headers=self._headers(connection), timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        payload = {
            "CardCode": payment.customer.code,
            "DocDate": payment.payment_date.isoformat(),
            "DocType": "rCustomer",
            "DocCurrency": payment.currency,
            "CashAccount": connection.config.get("cash_account", "") if payment.payment_method == "cash" else "",
            "TransferAccount": connection.config.get("bank_account", "") if payment.payment_method in ("neft", "rtgs", "imps", "upi") else "",
            "TransferSum": float(payment.amount) if payment.payment_method != "cash" else 0,
            "CashSum": float(payment.amount) if payment.payment_method == "cash" else 0,
            "Reference1": payment.reference,
            "Reference2": payment.payment_number,
            "Remarks": payment.notes or "",
            "PaymentInvoices": [
                {"DocEntry": a.invoice.metadata.get("sap_doc_entry", 0),
                 "SumApplied": float(a.amount)}
                for a in payment.allocations.all()
            ],
        }
        resp = requests.post(urljoin(self._base_url(connection), "IncomingPayments"),
                             headers=self._headers(connection), json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return {"success": True, "ref": str(resp.json().get("DocEntry", ""))}
        return {"success": False, "error": resp.text}

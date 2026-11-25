"""
Wave Financial connector.

OAuth 2.0 + Wave GraphQL API.
Docs: https://developer.wave.com/
"""
import logging
import time
from typing import List, Dict, Any

import requests

from apps.integrations.base import BaseConnector, register_connector

log = logging.getLogger("payreceivio.wave")


@register_connector
class WaveConnector(BaseConnector):
    name = "wave"
    label = "Wave Financial"
    vendor = "Wave Financial"
    supported_entities = ["customer", "invoice", "credit_note", "receipt"]

    GRAPHQL_URL = "https://gql.waveapps.com/graphql/public"
    AUTH_URL = "https://api.waveapps.com/oauth2/token/"

    def _refresh_token(self, connection) -> str:
        refresh_token = connection.credentials.get("refresh_token")
        client_id = connection.credentials.get("client_id")
        client_secret = connection.credentials.get("client_secret")
        if not all([refresh_token, client_id, client_secret]):
            raise ValueError("Missing Wave OAuth credentials")
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
        }

    def _graphql(self, connection, query: str, variables: dict = None) -> dict:
        resp = requests.post(self.GRAPHQL_URL,
            headers=self._headers(connection),
            json={"query": query, "variables": variables or {}},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def authenticate(self, connection) -> bool:
        try:
            self._access_token(connection)
            return True
        except Exception as e:
            log.error(f"Wave auth failed: {e}")
            return False

    def test_connection(self, connection) -> bool:
        try:
            result = self._graphql(connection, "query { user { id firstName } }")
            return "data" in result
        except Exception:
            return False

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        business_id = connection.config.get("business_id", "")
        query = f"""
        query {{
          business(id: "{business_id}") {{
            customers {{
              edges {{
                node {{
                  id
                  name
                  email
                  mobile
                  taxId
                }}
              }}
            }}
          }}
        }}
        """
        result = self._graphql(connection, query)
        return [e["node"] for e in result.get("data", {}).get("business", {}).get("customers", {}).get("edges", [])]

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        business_id = connection.config.get("business_id", "")
        query = f"""
        query {{
          business(id: "{business_id}") {{
            invoices(status: UNPAID) {{
              edges {{
                node {{
                  id
                  invoiceNumber
                  customer {{ id name }}
                  issueDate
                  dueDate
                  amountDue {{ value currency }}
                  total {{ value currency }}
                }}
              }}
            }}
          }}
        }}
        """
        result = self._graphql(connection, query)
        return [e["node"] for e in result.get("data", {}).get("business", {}).get("invoices", {}).get("edges", [])]

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        business_id = connection.config.get("business_id", "")
        query = f"""
        query {{
          business(id: "{business_id}") {{
            payments {{
              edges {{
                node {{
                  id
                  amount {{ value currency }}
                  paymentDate
                  method
                  note
                }}
              }}
            }}
          }}
        }}
        """
        result = self._graphql(connection, query)
        return [e["node"] for e in result.get("data", {}).get("business", {}).get("payments", {}).get("edges", [])]

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        business_id = connection.config.get("business_id", "")
        customer_id = payment.customer.metadata.get("wave_id", "")
        invoice_id = ""
        if payment.allocations.first():
            invoice_id = payment.allocations.first().invoice.metadata.get("wave_id", "")
        mutation = """
        mutation CreatePayment($input: MoneyPaymentCreateInput!) {
          moneyPaymentCreate(input: $input) {
            didSucceed
            payment { id }
            errors { message }
          }
        }
        """
        variables = {
            "input": {
                "businessId": business_id,
                "customerId": customer_id,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "paymentDate": payment.payment_date.isoformat(),
                "paymentMethod": self._map_method(payment.payment_method),
                "note": payment.notes or "",
                "invoiceId": invoice_id or None,
            }
        }
        result = self._graphql(connection, mutation, variables)
        if result.get("data", {}).get("moneyPaymentCreate", {}).get("didSucceed"):
            return {"success": True, "ref": result["data"]["moneyPaymentCreate"]["payment"]["id"]}
        return {"success": False, "error": str(result.get("errors"))}

    def _map_method(self, method: str) -> str:
        return {"upi": "UPI", "neft": "BANK", "rtgs": "BANK", "imps": "BANK",
                "cheque": "CHECK", "cash": "CASH", "card": "CREDIT_CARD"}.get(method, "OTHER")

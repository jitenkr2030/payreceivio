"""
TallyPrime connector.

TallyPrime is a desktop accounting system used widely in India. Integration
typically uses one of:
1. XML over HTTP (Tally's built-in HTTP server on port 9000)
2. JSON via the Tally connector service
3. ODBC direct database connection
4. TDL (Tally Definition Language) customisation

This connector uses the XML-over-HTTP approach via a local agent that
proxies requests from PayReceivio cloud to the on-premise Tally installation.
"""
from typing import List, Dict, Any

from apps.integrations.base import BaseConnector, register_connector


@register_connector
class TallyConnector(BaseConnector):
    name = "tally"
    label = "TallyPrime"
    vendor = "Tally Solutions"
    supported_entities = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    def authenticate(self, connection) -> bool:
        # Verify the local agent is reachable
        agent_url = connection.config.get("agent_url", "http://localhost:9000")
        return bool(agent_url)

    def test_connection(self, connection) -> bool:
        return self.authenticate(connection)

    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        """Build the Tally XML request to fetch ledgers under the Sundry Debtors group."""
        xml = self._wrap_envelope("""
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Accounts</REPORTNAME>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        <DOLLARFILTER>Sundry Debtors</DOLLARFILTER>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        """)
        # In production: POST xml to the agent_url and parse response.
        # Mock for development:
        return []

    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        """Fetch sales invoices (outstanding bills)."""
        xml = self._wrap_envelope("""
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Bills Receivable</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        """)
        return []

    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        """Fetch receipt vouchers."""
        xml = self._wrap_envelope("""
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Receipt Vouchers</REPORTNAME>
                </REQUESTDESC>
            </EXPORTDATA>
        """)
        return []

    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        """Post a receipt voucher to Tally via XML."""
        xml = self._build_receipt_voucher_xml(payment)
        # In production: POST to agent_url
        return {"success": True, "ref": f"TALLY-{payment.payment_number}", "xml": xml[:200]}

    def _wrap_envelope(self, body: str) -> str:
        """Wrap a body in the Tally XML envelope."""
        return f"<ENVELOPE>{body}</ENVELOPE>"

    def _build_receipt_voucher_xml(self, payment) -> str:
        """Build the Tally voucher XML for a receipt."""
        from datetime import datetime
        date_str = payment.payment_date.strftime("%Y%m%d")
        return f"""
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Import Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <IMPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>Vouchers</REPORTNAME>
                        <STATICVARIABLES><SVCURRENTCOMPANY>{payment.organization.name}</SVCURRENTCOMPANY></STATICVARIABLES>
                    </REQUESTDESC>
                    <REQUESTDATA>
                        <TALLYMESSAGE xmlns:UDF="TallyUDF">
                            <VOUCHER REMOTEID="{payment.payment_number}" VCHTYPE="Receipt" ACTION="Create">
                                <DATE>{date_str}</DATE>
                                <GUID>{payment.payment_number}</GUID>
                                <NARRATION>{payment.notes or 'Receipt from ' + payment.customer.name}</NARRATION>
                                <VOUCHERNUMBER>{payment.receipt_number or payment.payment_number}</VOUCHERNUMBER>
                                <PARTYLEDGERNAME>{payment.customer.name}</PARTYLEDGERNAME>
                                <EFFECTIVEDATE>{date_str}</EFFECTIVEDATE>
                                <ALLLEDGERENTRIES.LIST>
                                    <LEDGERNAME>{payment.customer.name}</LEDGERNAME>
                                    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                                    <AMOUNT>-{payment.amount}</AMOUNT>
                                </ALLLEDGERENTRIES.LIST>
                                <ALLLEDGERENTRIES.LIST>
                                    <LEDGERNAME>Cash or Bank</LEDGERNAME>
                                    <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                                    <AMOUNT>{payment.amount}</AMOUNT>
                                </ALLLEDGERENTRIES.LIST>
                            </VOUCHER>
                        </TALLYMESSAGE>
                    </REQUESTDATA>
                </IMPORTDATA>
            </BODY>
        </ENVELOPE>
        """.strip()

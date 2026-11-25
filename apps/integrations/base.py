"""
Base connector interface - all accounting connectors implement this.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseConnector(ABC):
    """Abstract base class for all accounting connectors."""

    name: str = ""
    label: str = ""
    vendor: str = ""
    supported_entities: List[str] = ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]

    @abstractmethod
    def authenticate(self, connection) -> bool:
        """Verify the connection credentials."""
        pass

    @abstractmethod
    def fetch_customers(self, connection, since=None) -> List[Dict[str, Any]]:
        """Fetch customers from accounting system."""
        pass

    @abstractmethod
    def fetch_invoices(self, connection, since=None) -> List[Dict[str, Any]]:
        """Fetch sales invoices (outstanding)."""
        pass

    @abstractmethod
    def fetch_receipts(self, connection, since=None) -> List[Dict[str, Any]]:
        """Fetch receipt vouchers."""
        pass

    @abstractmethod
    def post_receipt(self, connection, payment) -> Dict[str, Any]:
        """Post a receipt voucher back to accounting system."""
        pass

    @abstractmethod
    def test_connection(self, connection) -> bool:
        """Test that the connection is alive."""
        pass


class MockConnector(BaseConnector):
    """Mock connector for development/testing."""

    name = "mock"
    label = "Mock Accounting"
    vendor = "Test"

    def authenticate(self, connection):
        return True

    def fetch_customers(self, connection, since=None):
        return []

    def fetch_invoices(self, connection, since=None):
        return []

    def fetch_receipts(self, connection, since=None):
        return []

    def post_receipt(self, connection, payment):
        return {"success": True, "ref": "MOCK-001"}

    def test_connection(self, connection):
        return True


# Registry of available connectors
CONNECTOR_REGISTRY: Dict[str, type] = {"mock": MockConnector}


def register_connector(connector_class: type):
    """Register a connector class."""
    CONNECTOR_REGISTRY[connector_class.name] = connector_class
    return connector_class


def get_connector(name: str) -> BaseConnector:
    """Get a connector instance by name."""
    cls = CONNECTOR_REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown connector: {name}")
    return cls()

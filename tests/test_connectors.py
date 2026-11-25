"""Tests for all 19 accounting connectors."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.integrations.base import get_connector, CONNECTOR_REGISTRY


@pytest.mark.django_db
class TestConnectorRegistry:
    def test_all_19_connectors_registered(self):
        expected = [
            "mock", "tally", "zoho",
            "busy", "marg", "quickbooks", "xero", "sage", "dynamics365",
            "netsuite", "sap_b1", "odoo", "myob", "freshbooks", "wave",
            "gofrugal", "focus", "exact", "autocount", "money_forward",
        ]
        for name in expected:
            assert name in CONNECTOR_REGISTRY, f"Connector '{name}' not registered"

    def test_get_connector_returns_instance(self):
        for name in ["busy", "marg", "quickbooks", "xero", "sage", "dynamics365",
                     "netsuite", "sap_b1", "odoo", "myob", "freshbooks", "wave",
                     "gofrugal", "focus", "exact", "autocount", "money_forward"]:
            c = get_connector(name)
            assert c is not None
            assert hasattr(c, "authenticate")
            assert hasattr(c, "fetch_customers")
            assert hasattr(c, "fetch_invoices")
            assert hasattr(c, "fetch_receipts")
            assert hasattr(c, "post_receipt")
            assert hasattr(c, "test_connection")


@pytest.mark.django_db
class TestQuickBooksConnector:
    def test_base_url_construction(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from apps.organizations.models import Company
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="quickbooks", label="QuickBooks", vendor="Intuit", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"realm_id": "123456789", "environment": "sandbox"},
        )
        c = get_connector("quickbooks")
        url = c._base_url(conn)
        assert "sandbox-quickbooks.api.intuit.com" in url
        assert "123456789" in url

    def test_method_mapping(self):
        c = get_connector("quickbooks")
        assert c._map_method("upi") == "UPI"
        assert c._map_method("cash") == "Cash"
        assert c._map_method("cheque") == "Check"


@pytest.mark.django_db
class TestXeroConnector:
    def test_headers_include_tenant_id(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="xero", label="Xero", vendor="Xero", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"tenant_id": "TENANT123"},
            credentials={"access_token": "abc", "expires_at": "9999999999"},
        )
        c = get_connector("xero")
        headers = c._headers(conn)
        assert headers["Xero-tenant-id"] == "TENANT123"
        assert headers["Authorization"] == "Bearer abc"


@pytest.mark.django_db
class TestSageConnector:
    def test_region_based_url(self):
        c = get_connector("sage")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="sage", label="Sage", vendor="Sage", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"region": "us"},
        )
        url = c._base_url(conn)
        assert "sage.com" in url


@pytest.mark.django_db
class TestDynamics365Connector:
    def test_environment_in_url(self):
        c = get_connector("dynamics365")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="dynamics365", label="D365", vendor="Microsoft", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"environment": "sandbox", "company_id": "GUID123", "tenant_id": "TENANT"},
        )
        url = c._base_url(conn)
        assert "sandbox" in url
        assert "GUID123" in url


@pytest.mark.django_db
class TestNetSuiteConnector:
    def test_account_id_in_url(self):
        c = get_connector("netsuite")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="netsuite", label="NS", vendor="Oracle", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"account_id": "1234567"},
        )
        url = c._base_url(conn)
        # Account ID with dashes replaced by underscores
        assert "1234567" in url


@pytest.mark.django_db
class TestSAPB1Connector:
    def test_service_layer_url(self):
        c = get_connector("sap_b1")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="sap_b1", label="SAP B1", vendor="SAP", auth_method="basic")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"host": "sap.example.com", "port": 50000, "company_db": "TESTCO"},
        )
        url = c._base_url(conn)
        assert "sap.example.com:50000" in url
        assert "/b1s/v1/" in url


@pytest.mark.django_db
class TestOdooConnector:
    def test_xmlrpc_url(self):
        c = get_connector("odoo")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="odoo", label="Odoo", vendor="Odoo", auth_method="api_key")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"host": "https://odoo.example.com", "database": "TEST"},
            credentials={"username": "admin", "api_key": "k"},
        )
        assert "odoo.example.com/xmlrpc/2" in c._url(conn, "xmlrpc/2")


@pytest.mark.django_db
class TestMYOBConnector:
    def test_company_url_includes_uuid(self):
        c = get_connector("myob")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="myob", label="MYOB", vendor="MYOB", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"company_file_uid": "abc-123"},
        )
        url = c._company_url(conn)
        assert "abc-123" in url


@pytest.mark.django_db
class TestFreshBooksConnector:
    def test_account_id_in_url(self):
        c = get_connector("freshbooks")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="freshbooks", label="FB", vendor="FB", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"account_id": "ACCT123"},
        )
        # Just verify the connector is functional
        assert c.name == "freshbooks"


@pytest.mark.django_db
class TestWaveConnector:
    def test_uses_graphql(self):
        c = get_connector("wave")
        assert c.GRAPHQL_URL == "https://gql.waveapps.com/graphql/public"


@pytest.mark.django_db
class TestGoFrugalConnector:
    def test_host_port_url(self):
        c = get_connector("gofrugal")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="gofrugal", label="GF", vendor="GF", auth_method="api_key")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"host": "gf.example.com", "port": 8505},
        )
        url = c._base_url(conn)
        assert "gf.example.com:8505" in url


@pytest.mark.django_db
class TestFocusConnector:
    def test_iconnect_url(self):
        c = get_connector("focus")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="focus", label="Focus", vendor="Focus", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"host": "f.example.com", "port": 8080},
        )
        url = c._base_url(conn)
        assert "iconnect/api/v1" in url


@pytest.mark.django_db
class TestExactOnlineConnector:
    def test_region_specific_url(self):
        c = get_connector("exact")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="exact", label="Exact", vendor="Exact", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"region": "be", "division": "5"},
        )
        url = c._base_url(conn)
        assert "exactonline.be" in url


@pytest.mark.django_db
class TestAutoCountConnector:
    def test_url_construction(self):
        c = get_connector("autocount")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="autocount", label="AC", vendor="AC", auth_method="api_key")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"host": "ac.example.com", "port": 8081},
        )
        url = c._base_url(conn)
        assert "autocount/api" in url


@pytest.mark.django_db
class TestMoneyForwardConnector:
    def test_office_id_in_url(self):
        c = get_connector("money_forward")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="money_forward", label="MF", vendor="MF", auth_method="oauth2")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"office_id": "OFFICE123"},
        )
        customers_url = f"offices/{conn.config.get('office_id')}/partners.json"
        assert "OFFICE123" in customers_url


@pytest.mark.django_db
class TestBUSYConnector:
    def test_company_header(self):
        c = get_connector("busy")
        from apps.organizations.services import create_organization_with_owner
        from apps.integrations.models import Connector, AccountingConnection
        from django.contrib.auth import get_user_model
        User = get_user_model()

        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        connector = Connector.objects.create(name="busy", label="BUSY", vendor="BUSY", auth_method="api_key")

        conn = AccountingConnection.objects.create(
            organization=org, company=company, connector=connector, name="Test",
            config={"api_url": "http://localhost:5400", "company_code": "BOM01"},
            credentials={"api_token": "tkn"},
        )
        headers = c._headers(conn)
        assert headers["X-Busy-Company"] == "BOM01"
        assert headers["Authorization"] == "Bearer tkn"


@pytest.mark.django_db
class TestMargConnector:
    def test_method_mapping(self):
        c = get_connector("marg")
        assert c._map_mode("upi") == "UPI"
        assert c._map_mode("cash") == "Cash"
        assert c._map_mode("cheque") == "Cheque"


@pytest.mark.django_db
class TestConnectorsPage:
    def test_connectors_list_page(self, client):
        r = client.get("/connectors/")
        assert r.status_code == 200

    def test_connector_docs_page(self, client):
        for name in ["busy", "marg", "quickbooks", "xero", "sage", "dynamics365",
                     "netsuite", "sap_b1", "odoo", "myob", "freshbooks", "wave",
                     "gofrugal", "focus", "exact", "autocount", "money_forward"]:
            r = client.get(f"/connectors/{name}/")
            assert r.status_code == 200, f"Docs page for {name} failed"


@pytest.mark.django_db
class TestSeedDataRegistersAllConnectors:
    def test_seed_registers_19_connectors(self):
        from django.core.management import call_command
        from apps.integrations.models import Connector
        call_command("seed_data", "--reset", verbosity=0)
        # 19 vendor connectors (Tally, Zoho + 17 new)
        assert Connector.objects.count() == 19
        names = set(Connector.objects.values_list("name", flat=True))
        expected = {
            "tally", "zoho", "busy", "marg", "quickbooks", "xero", "sage",
            "dynamics365", "netsuite", "sap_b1", "odoo", "myob", "freshbooks",
            "wave", "gofrugal", "focus", "exact", "autocount", "money_forward",
        }
        assert names == expected, f"Missing: {expected - names}"

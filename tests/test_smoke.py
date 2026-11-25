"""Smoke tests for PayReceivio - models, services, RBAC, tenancy."""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self):
        u = User.objects.create_user(
            email="t@t.com", password="Test@12345", full_name="Test User"
        )
        assert u.pk is not None
        assert u.email == "t@t.com"
        assert u.check_password("Test@12345")
        assert u.display_name == "Test User"

    def test_user_normalize_email(self):
        u = User.objects.create_user(
            email="Test@Example.COM", password="Test@12345", full_name="T"
        )
        assert u.email == "Test@example.com"


@pytest.mark.django_db
class TestOrganizationAndTenancy:
    def test_create_organization_with_owner(self):
        from apps.organizations.services import create_organization_with_owner
        owner = User.objects.create_user(
            email="owner@t.com", password="Test@12345", full_name="Owner"
        )
        org = create_organization_with_owner("Test Org Inc", owner)
        assert org.pk is not None
        assert org.name == "Test Org Inc"
        assert org.companies.count() == 1
        assert org.companies.first().branches.count() == 1
        # Role assignment
        assert owner.role_assignments.count() == 1
        assert owner.role_assignments.first().role.name == "org_owner"
        # All system roles seeded
        assert org.roles.count() == 10  # 11 system roles minus super_admin


@pytest.mark.django_db
class TestCustomerAndAgeing:
    def test_customer_outstanding_and_ageing(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.customers.models import Customer, CustomerLedgerEntry
        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        c = Customer.objects.create(
            organization=org, company=company, code="C001",
            name="Test Customer", credit_limit=Decimal("100000"),
            credit_period_days=30, created_by=owner, updated_by=owner,
        )
        # Add invoice amount via ledger
        CustomerLedgerEntry.objects.create(
            organization=org, company=company, customer=c,
            entry_type="invoice", entry_date=date.today(),
            amount=Decimal("50000"), reference="INV-001",
            created_by=owner,
        )
        assert c.outstanding_balance == Decimal("50000")
        ageing = __import__("apps.customers.services", fromlist=["compute_customer_ageing"]).compute_customer_ageing(c)
        assert ageing["total"] == Decimal("0")  # no real invoices in db yet


@pytest.mark.django_db
class TestPaymentAndAllocation:
    def test_record_payment_idempotent(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.customers.models import Customer
        from apps.payments.services import record_payment
        from apps.payments.models import Payment
        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        c = Customer.objects.create(
            organization=org, company=company, code="C001", name="Test Cust",
            created_by=owner, updated_by=owner,
        )
        p = record_payment(
            organization=org, customer=c, amount=Decimal("10000"),
            payment_date=date.today(), payment_method="upi",
            reference="UTR123", received_by=owner,
        )
        assert p.pk is not None
        assert p.amount == Decimal("10000")
        assert p.payment_number.startswith("RCT/")
        assert p.receipt_number.startswith("RCP/")
        # Ledger entry created
        assert c.ledger_entries.count() == 1
        assert c.outstanding_balance == Decimal("-10000")  # customer has credit


@pytest.mark.django_db
class TestReconciliationEngine:
    def test_csv_import_and_auto_match(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.customers.models import Customer
        from apps.payments.services import record_payment
        from apps.reconciliation.models import BankAccount, BankTransaction
        from apps.reconciliation.services import import_bank_statement_csv, auto_match_transactions
        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        company = org.companies.first()
        c = Customer.objects.create(
            organization=org, company=company, code="C001", name="Test Cust",
            created_by=owner, updated_by=owner,
        )
        # Record a payment with UTR
        p = record_payment(
            organization=org, customer=c, amount=Decimal("5000"),
            payment_date=date.today(), payment_method="neft",
            reference="UTRABC123", received_by=owner,
        )
        # Bank account
        bank = BankAccount.objects.create(
            organization=org, company=company,
            account_name="Test Bank", bank_name="HDFC",
            account_number="12345", created_by=owner, updated_by=owner,
        )
        # Import CSV with the matching UTR
        rows = [{
            "date": date.today().isoformat(),
            "amount": "5000", "type": "credit",
            "description": "NEFT Credit Test Cust",
            "reference": "UTRABC123", "utr": "UTRABC123",
        }]
        stmt = import_bank_statement_csv(org, bank, rows, statement_date=date.today(), user=owner)
        # The transaction should be auto-matched via UTR
        txn = BankTransaction.objects.get(statement=stmt)
        assert txn.status == "matched", f"Expected matched, got {txn.status}"
        assert txn.matched_payment_id == p.pk


@pytest.mark.django_db
class TestAIAssistant:
    def test_answer_question_overdue(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.ai_assistant.services import answer_question
        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        result = answer_question("How much money is overdue today?", org, owner)
        assert result["intent"] == "total_overdue"
        assert "Total overdue today" in result["answer"]

    def test_answer_question_help(self):
        from apps.organizations.services import create_organization_with_owner
        from apps.ai_assistant.services import answer_question
        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        result = answer_question("what can you do?", org, owner)
        assert result["intent"] == "help"


@pytest.mark.django_db
class TestPublicPages:
    def test_landing_page(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_login_page(self, client):
        r = client.get("/accounts/login/")
        assert r.status_code == 200

    def test_signup_page(self, client):
        r = client.get("/accounts/signup/")
        assert r.status_code == 200

    def test_portal_login_page(self, client):
        r = client.get("/portal/login/")
        assert r.status_code == 200


@pytest.mark.django_db
class TestSubscriptionPlans:
    def test_plan_defaults(self):
        from apps.subscriptions.models import Plan, PlanDefaults
        for p in PlanDefaults.DEFAULTS:
            Plan.objects.update_or_create(name=p["name"], defaults=p)
        assert Plan.objects.count() >= 6
        trial = Plan.objects.get(name="trial")
        assert trial.is_trial
        assert trial.trial_days == 14
        starter = Plan.objects.get(name="starter")
        assert starter.monthly_price == Decimal("999")


@pytest.mark.django_db
class TestConnectors:
    def test_tally_connector_xml(self):
        from apps.integrations.base import get_connector
        from apps.organizations.services import create_organization_with_owner
        from apps.customers.models import Customer
        from apps.payments.services import record_payment
        owner = User.objects.create_user(email="o@t.com", password="Test@12345", full_name="O")
        org = create_organization_with_owner("Test", owner)
        c = Customer.objects.create(organization=org, code="C1", name="T",
                                     company=org.companies.first(), created_by=owner, updated_by=owner)
        p = record_payment(organization=org, customer=c, amount=Decimal("1000"),
                           payment_date=date.today(), payment_method="cash", received_by=owner)
        connector = get_connector("tally")
        xml = connector._build_receipt_voucher_xml(p)
        assert "<ENVELOPE>" in xml
        assert "<VOUCHER" in xml
        assert "Receipt" in xml
        assert p.payment_number in xml

    def test_zoho_connector_token_refresh_logic(self):
        from apps.integrations.base import get_connector
        connector = get_connector("zoho")
        assert connector.name == "zoho"
        assert "zohoapis" in connector.BASE_URLS["in"]

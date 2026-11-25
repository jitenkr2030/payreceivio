"""
Seed PayReceivio with comprehensive demo data:
- 1 organization + 2 companies + 3 branches
- 3 users per role
- 50 customers
- 200 invoices (mix of unpaid/paid/overdue)
- 80 payments (with allocations)
- 1 bank statement with 50 transactions
- 1 reconciliation match
- 5 collection tasks + follow-ups + promises
- 5 message templates
- Subscription plan defaults
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed PayReceivio with comprehensive demo data"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting data...")
            self._reset()

        self.stdout.write(self.style.SUCCESS("Seeding PayReceivio demo data..."))

        # Plans
        self._seed_plans()

        # Connectors
        self._seed_connectors()

        # Organization + owner
        org, owner = self._seed_organization()

        # Companies + branches
        companies = self._seed_companies(org, owner)

        # Users with roles
        users = self._seed_users(org, owner, companies)

        # Customers
        customers = self._seed_customers(org, companies, users)

        # Invoices
        invoices = self._seed_invoices(org, customers, users)

        # Payments + allocations
        payments = self._seed_payments(org, customers, invoices, users)

        # Bank statements + reconciliation
        self._seed_bank_data(org, companies, payments, users)

        # Collection tasks + follow-ups + promises
        self._seed_collections(org, customers, invoices, users)

        # Message templates
        self._seed_templates(org, owner)

        # Subscription
        self._seed_subscription(org)

        # Customer portal users
        self._seed_portal_users(org, customers)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created:\n"
            f"  - 1 organization: {org.name}\n"
            f"  - {len(companies)} companies\n"
            f"  - {len(users)} users (login: see below)\n"
            f"  - {len(customers)} customers\n"
            f"  - {len(invoices)} invoices\n"
            f"  - {len(payments)} payments\n"
            f"  - Message templates\n"
            f"  - Subscription plans\n\n"
            f"Default logins:\n"
            f"  Owner: owner@demo.com / Demo@12345\n"
            f"  Finance Manager: finance@demo.com / Demo@12345\n"
            f"  Collection Exec: collections@demo.com / Demo@12345\n"
            f"  Salesperson: sales@demo.com / Demo@12345\n"
            f"  Customer Portal: customer1@demo.com / Demo@12345\n"
        ))

    def _reset(self):
        from apps.customer_portal.models import PortalUser
        from apps.communications.models import MessageTemplate, Message, Campaign
        from apps.collections.models import CollectionTask, FollowUp, PromiseToPay
        from apps.reconciliation.models import BankAccount, BankStatement, BankTransaction
        from apps.payments.models import Payment, PaymentLink
        from apps.receivables.models import Invoice, CreditNote, InvoiceAllocation
        from apps.customers.models import Customer, CustomerLedgerEntry
        from apps.subscriptions.models import Subscription, Plan
        from apps.integrations.models import Connector, AccountingConnection
        PortalUser.objects.all().delete()
        MessageTemplate.objects.all().delete()
        Message.objects.all().delete()
        Campaign.objects.all().delete()
        CollectionTask.objects.all().delete()
        FollowUp.objects.all().delete()
        PromiseToPay.objects.all().delete()
        BankTransaction.objects.all().delete()
        BankStatement.objects.all().delete()
        BankAccount.objects.all().delete()
        Payment.objects.all().delete()
        PaymentLink.objects.all().delete()
        InvoiceAllocation.objects.all().delete()
        Invoice.objects.all().delete()
        CreditNote.objects.all().delete()
        CustomerLedgerEntry.objects.all().delete()
        Customer.objects.all().delete()
        Subscription.objects.all().delete()
        AccountingConnection.objects.all().delete()
        Connector.objects.all().delete()
        Plan.objects.all().delete()
        User.objects.filter(email__endswith="@demo.com").delete()
        from apps.organizations.models import Organization
        Organization.objects.all().delete()

    def _seed_plans(self):
        from apps.subscriptions.models import Plan, PlanDefaults
        for p in PlanDefaults.DEFAULTS:
            Plan.objects.update_or_create(
                name=p["name"],
                defaults={**p, "is_active": True, "sort_order": {"trial": 0, "starter": 1, "growth": 2, "professional": 3, "business": 4, "enterprise": 5}.get(p["name"], 99)}
            )
        self.stdout.write("  + Subscription plans")

    def _seed_connectors(self):
        from apps.integrations.models import Connector
        connectors = [
            ("tally", "TallyPrime", "Tally Solutions", "local_agent",
             ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]),
            ("zoho", "Zoho Books", "Zoho", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("busy", "BUSY", "BUSY Infotech", "api_key",
             ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]),
            ("marg", "Marg ERP", "Marg Compusolutions", "api_key",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("quickbooks", "QuickBooks Online", "Intuit", "oauth2",
             ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]),
            ("xero", "Xero", "Xero", "oauth2",
             ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]),
            ("sage", "Sage Business Cloud", "Sage Group", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("dynamics365", "Microsoft Dynamics 365 Business Central", "Microsoft", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("netsuite", "Oracle NetSuite", "Oracle", "oauth2",
             ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]),
            ("sap_b1", "SAP Business One", "SAP", "basic",
             ["customer", "invoice", "credit_note", "receipt", "ledger_balance"]),
            ("odoo", "Odoo", "Odoo S.A.", "api_key",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("myob", "MYOB AccountRight", "MYOB", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("freshbooks", "FreshBooks", "FreshBooks", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("wave", "Wave Financial", "Wave Financial", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("gofrugal", "GoFrugal", "GoFrugal Technologies", "api_key",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("focus", "Focus Softnet (Focus 9/i)", "Focus Softnet", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("exact", "Exact Online", "Exact", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("autocount", "AutoCount", "AutoCount Sdn Bhd", "api_key",
             ["customer", "invoice", "credit_note", "receipt"]),
            ("money_forward", "Money Forward Cloud", "Money Forward", "oauth2",
             ["customer", "invoice", "credit_note", "receipt"]),
        ]
        for name, label, vendor, auth, entities in connectors:
            Connector.objects.update_or_create(
                name=name,
                defaults={"label": label, "vendor": vendor, "auth_method": auth,
                          "supported_entities": entities, "is_active": True}
            )
        self.stdout.write(f"  + {len(connectors)} accounting connectors")

    def _seed_organization(self):
        from apps.organizations.models import Organization
        from apps.organizations.services import create_organization_with_owner

        org = Organization.objects.filter(name="Acme Manufacturing Pvt Ltd").first()
        if org:
            owner = User.objects.get(email="owner@demo.com")
            return org, owner

        owner = User.objects.create_user(
            email="owner@demo.com",
            password="Demo@12345",
            full_name="Rajesh Kumar (Owner)",
            phone="+919876543210",
        )
        org = create_organization_with_owner("Acme Manufacturing Pvt Ltd", owner)
        org.legal_name = "Acme Manufacturing Private Limited"
        org.gst_number = "27AABCA1234B1Z5"
        org.address_line1 = "Plot 14, MIDC Industrial Area"
        org.city = "Mumbai"
        org.state = "Maharashtra"
        org.country = "India"
        org.postal_code = "400093"
        org.save()
        self.stdout.write(f"  + Organization: {org.name}")
        return org, owner

    def _seed_companies(self, org, owner):
        from apps.organizations.models import Company, Branch
        c1 = Company.objects.create(
            organization=org, name="Acme Manufacturing - Mumbai",
            legal_name="Acme Manufacturing Pvt Ltd - Mumbai Unit",
            gst_number="27AABCA1234B1Z5", city="Mumbai", state="Maharashtra",
            country="India", created_by=owner, updated_by=owner,
        )
        c2 = Company.objects.create(
            organization=org, name="Acme Trading - Delhi",
            legal_name="Acme Trading LLP",
            gst_number="07AABCA5678B1Z2", city="New Delhi", state="Delhi",
            country="India", created_by=owner, updated_by=owner,
        )
        Branch.objects.create(company=c1, name="Mumbai HO", code="BOM-HO", is_head_office=True, city="Mumbai", created_by=owner, updated_by=owner)
        Branch.objects.create(company=c1, name="Pune Branch", code="PNR", city="Pune", created_by=owner, updated_by=owner)
        Branch.objects.create(company=c2, name="Delhi HO", code="DEL-HO", is_head_office=True, city="New Delhi", created_by=owner, updated_by=owner)
        self.stdout.write("  + 2 companies, 3 branches")
        return list(Company.objects.filter(organization=org))

    def _seed_users(self, org, owner, companies):
        from apps.accounts.models import Role, RoleAssignment
        users = [owner]
        roles_to_create = [
            ("finance@demo.com", "Priya Sharma", "Finance Manager", "finance_manager"),
            ("accountant@demo.com", "Amit Patel", "Accountant", "accountant"),
            ("collection_mgr@demo.com", "Sunita Reddy", "Collection Manager", "collection_manager"),
            ("collections@demo.com", "Vikram Singh", "Collection Executive", "collection_executive"),
            ("sales_mgr@demo.com", "Rohit Mehta", "Sales Manager", "sales_manager"),
            ("sales@demo.com", "Anita Gupta", "Salesperson", "salesperson"),
            ("sales2@demo.com", "Deepak Yadav", "Salesperson", "salesperson"),
            ("auditor@demo.com", "Kavita Iyer", "Auditor", "auditor"),
        ]
        for email, name, label, role_name in roles_to_create:
            u = User.objects.create_user(
                email=email, password="Demo@12345", full_name=name,
                phone=f"+9198765{random.randint(10000, 99999)}",
            )
            role = Role.objects.get(organization=org, name=role_name)
            RoleAssignment.objects.create(
                user=u, role=role, organization=org, company=companies[0], assigned_by=owner,
            )
            users.append(u)
        self.stdout.write(f"  + {len(users)} users")
        return users

    def _seed_customers(self, org, companies, users):
        from apps.customers.models import Customer
        from apps.organizations.models import Branch
        salespeople = [u for u in users if u.email in ("sales@demo.com", "sales2@demo.com")]
        branches = list(Branch.objects.filter(company__organization=org))

        first_names = ["Sharma", "Verma", "Gupta", "Patel", "Reddy", "Nair", "Iyer", "Mehta",
                       "Joshi", "Kapoor", "Bhat", "Rao", "Das", "Sen", "Bose", "Khan", "Sheikh",
                       "Pillai", "Menon", "Kaur", "Anand", "Malhotra", "Agarwal", "Saxena",
                       "Chopra", "Banerjee", "Mukherjee", "Ghosh", "Shah", "Desai"]
        cities = [("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"), ("Delhi", "Delhi"),
                  ("Bangalore", "Karnataka"), ("Chennai", "Tamil Nadu"), ("Hyderabad", "Telangana"),
                  ("Ahmedabad", "Gujarat"), ("Kolkata", "West Bengal"), ("Jaipur", "Rajasthan"),
                  ("Surat", "Gujarat")]

        customers = []
        for i in range(50):
            name = f"{random.choice(first_names)} Traders"
            if i < 5:
                name = f"{random.choice(first_names)} Industries Pvt Ltd"
            elif i < 15:
                name = f"{random.choice(first_names)} & Sons"
            city, state = random.choice(cities)
            branch = random.choice(branches)
            c = Customer.objects.create(
                organization=org, company=branch.company, branch=branch,
                code=f"CUST-{i+1:04d}",
                name=name,
                legal_name=name,
                email=f"contact{i+1}@example.com",
                phone=f"+9198{random.randint(10000000, 99999999)}",
                whatsapp_number=f"+9198{random.randint(10000000, 99999999)}",
                gst_number=f"27AABCA{random.randint(1000, 9999)}B1Z5" if i % 3 != 0 else "",
                billing_address=f"{random.randint(1, 200)}, Business Street, {city}",
                city=city, state=state, country="India",
                postal_code=f"{random.randint(400001, 599999)}",
                credit_limit=Decimal(str(random.choice([50000, 100000, 200000, 500000, 1000000]))),
                credit_period_days=random.choice([15, 30, 45, 60]),
                salesperson=random.choice(salespeople),
                risk_category=random.choices(["low", "medium", "high"], weights=[5, 3, 2])[0],
                created_by=users[0], updated_by=users[0],
            )
            customers.append(c)
        self.stdout.write(f"  + {len(customers)} customers")
        return customers

    def _seed_invoices(self, org, customers, users):
        from apps.receivables.models import Invoice
        from apps.receivables.services import generate_invoice_number
        from apps.customers.models import CustomerLedgerEntry
        today = date.today()
        invoices = []
        for i in range(200):
            customer = random.choice(customers)
            inv_date = today - timedelta(days=random.randint(1, 180))
            due_date = inv_date + timedelta(days=customer.credit_period_days)
            subtotal = Decimal(str(random.choice([15000, 25000, 42000, 58000, 75000, 100000, 125000, 150000, 200000, 350000])))
            tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
            total = subtotal + tax
            inv = Invoice.objects.create(
                organization=org, company=customer.company, branch=customer.branch,
                invoice_number=generate_invoice_number(org),
                customer=customer, invoice_date=inv_date, due_date=due_date,
                subtotal=subtotal, tax_amount=tax, total_amount=total,
                outstanding_amount=total,
                currency="INR", status="unpaid",
                payment_terms=f"{customer.credit_period_days} days",
                salesperson=customer.salesperson,
                created_by=users[0], updated_by=users[0],
            )
            # Ledger entry
            CustomerLedgerEntry.objects.create(
                organization=org, company=customer.company, branch=customer.branch,
                customer=customer, entry_type="invoice", entry_date=inv_date,
                amount=total, reference=inv.invoice_number,
                description=f"Sales invoice {inv.invoice_number}",
                related_invoice=inv, created_by=users[0],
            )
            invoices.append(inv)
        self.stdout.write(f"  + {len(invoices)} invoices")
        return invoices

    def _seed_payments(self, org, customers, invoices, users):
        from apps.payments.models import Payment
        from apps.payments.services import record_payment, allocate_payment
        from apps.receivables.services import update_invoice_status
        today = date.today()
        payments = []
        # Pick ~80 fully-paid and ~30 partially-paid invoices; rest unpaid
        paid_invoices = random.sample(invoices, 80)
        partial_invoices = random.sample([i for i in invoices if i not in paid_invoices], 30)
        for inv in paid_invoices:
            payment_date = inv.invoice_date + timedelta(days=random.randint(5, inv.customer.credit_period_days + 30))
            if payment_date > today:
                payment_date = today - timedelta(days=random.randint(1, 10))
            method = random.choices(["upi", "neft", "rtgs", "cheque", "cash"], weights=[4, 3, 1, 1, 1])[0]
            p = record_payment(
                organization=org, customer=inv.customer, amount=inv.total_amount,
                payment_date=payment_date, payment_method=method,
                reference=f"UTR{random.randint(100000000000, 999999999999)}",
                received_by=users[0], notes=f"Payment for {inv.invoice_number}",
                request=None,
            )
            allocate_payment(p, [{"invoice_id": inv.id, "amount": inv.total_amount}], user=users[0])
            update_invoice_status(inv)
            payments.append(p)
        for inv in partial_invoices:
            payment_date = inv.invoice_date + timedelta(days=random.randint(5, inv.customer.credit_period_days))
            if payment_date > today:
                payment_date = today - timedelta(days=random.randint(1, 10))
            partial_amt = (inv.total_amount * Decimal(str(random.choice([0.3, 0.5, 0.7])))).quantize(Decimal("0.01"))
            method = random.choice(["upi", "neft", "cheque"])
            p = record_payment(
                organization=org, customer=inv.customer, amount=partial_amt,
                payment_date=payment_date, payment_method=method,
                reference=f"UTR{random.randint(100000000000, 999999999999)}",
                received_by=users[0], notes=f"Part payment for {inv.invoice_number}",
                request=None,
            )
            allocate_payment(p, [{"invoice_id": inv.id, "amount": partial_amt}], user=users[0])
            update_invoice_status(inv)
            payments.append(p)
        self.stdout.write(f"  + {len(payments)} payments")
        return payments

    def _seed_bank_data(self, org, companies, payments, users):
        from apps.reconciliation.models import BankAccount, BankStatement, BankTransaction
        from apps.reconciliation.services import import_bank_statement_csv, auto_match_transactions
        owner = users[0]
        bank = BankAccount.objects.create(
            organization=org, company=companies[0],
            account_name="HDFC Bank - Current",
            bank_name="HDFC Bank", account_number="501000123456789",
            ifsc_code="HDFC0001234", branch_name="Mumbai Fort",
            created_by=owner, updated_by=owner,
        )
        # Build CSV-style rows from payments
        rows = []
        for p in random.sample(payments, min(50, len(payments))):
            rows.append({
                "date": p.payment_date.isoformat(),
                "amount": str(p.amount),
                "type": "credit",
                "description": f"NEFT/Credit from {p.customer.name} - {p.reference}",
                "reference": p.reference,
                "utr": p.reference,
                "counterparty": p.customer.name,
            })
        # Add some unmatched (bank charges, unrelated)
        for i in range(10):
            rows.append({
                "date": (date.today() - timedelta(days=random.randint(1, 30))).isoformat(),
                "amount": str(random.choice([100, 250, 500, 1500])),
                "type": "debit",
                "description": f"Bank charges/ATM/SMS charges - {i}",
                "reference": "",
                "utr": "",
                "counterparty": "HDFC Bank",
            })
        stmt = import_bank_statement_csv(org, bank, rows, statement_date=date.today(), user=owner)
        auto_match_transactions(org)
        self.stdout.write(f"  + Bank account, {len(rows)} transactions")

    def _seed_collections(self, org, customers, invoices, users):
        from apps.collections.models import CollectionTask, FollowUp, PromiseToPay
        overdue_invoices = [i for i in invoices if i.status == "overdue"]
        collection_exec = next(u for u in users if u.email == "collections@demo.com")
        for inv in random.sample(overdue_invoices, min(5, len(overdue_invoices))):
            task = CollectionTask.objects.create(
                organization=org, company=inv.customer.company, branch=inv.customer.branch,
                title=f"Follow up on overdue invoice {inv.invoice_number}",
                description=f"Customer {inv.customer.name} has ₹{inv.outstanding_amount} outstanding. Please follow up.",
                customer=inv.customer, invoice=inv,
                assigned_to=collection_exec, task_type="call",
                priority=random.choice(["medium", "high", "urgent"]),
                due_date=date.today() + timedelta(days=random.randint(0, 7)),
                created_by=users[0], updated_by=users[0],
            )
            FollowUp.objects.create(
                organization=org, customer=inv.customer, invoice=inv,
                channel="call", outcome=random.choice(["no_response", "promise_to_pay", "callback_requested"]),
                notes="Called customer, waiting for response.",
                followed_up_by=collection_exec,
                created_by=users[0], updated_by=users[0],
            )
            PromiseToPay.objects.create(
                organization=org, customer=inv.customer, invoice=inv,
                amount=inv.outstanding_amount,
                promised_date=date.today() + timedelta(days=random.randint(3, 15)),
                recorded_by=collection_exec,
                created_by=users[0], updated_by=users[0],
            )
        self.stdout.write("  + 5 collection tasks + follow-ups + promises")

    def _seed_templates(self, org, owner):
        from apps.communications.models import MessageTemplate
        templates = [
            ("Invoice Reminder", "invoice_reminder", "whatsapp",
             "Invoice Reminder - {{invoice_number}}",
             "Dear {{customer_name}},\n\nThis is a gentle reminder that invoice {{invoice_number}} for {{currency_symbol}}{{invoice_amount}} was due on {{due_date}}.\n\nOutstanding: {{currency_symbol}}{{outstanding_amount}}\n\nKindly arrange payment at your earliest convenience.\n\nThank you,\n{{organization_name}}"),
            ("Overdue Reminder", "overdue_reminder", "whatsapp",
             "Overdue Payment - {{invoice_number}}",
             "Dear {{customer_name}},\n\nYour invoice {{invoice_number}} for {{currency_symbol}}{{outstanding_amount}} is now {{days_overdue}} days overdue.\n\nPlease arrange payment immediately to avoid further escalation.\n\nThank you,\n{{organization_name}}"),
            ("Payment Confirmation", "payment_confirmation", "email",
             "Payment Received - {{payment_number}}",
             "Dear {{customer_name}},\n\nWe have received your payment of {{currency_symbol}}{{payment_amount}} via {{payment_method}} on {{payment_date}}.\n\nReceipt Number: {{receipt_number}}\n\nThank you for your prompt payment.\n\n{{organization_name}}"),
            ("Statement Share", "statement_share", "email",
             "Account Statement - {{organization_name}}",
             "Dear {{customer_name}},\n\nPlease find attached your account statement as of {{today}}.\n\nIf you have any questions, please contact us.\n\n{{organization_name}}"),
            ("Payment Link", "payment_link", "whatsapp",
             "Payment Link",
             "Dear {{customer_name}},\n\nPlease click the link below to make a payment:\n\n{{payment_link}}\n\nThank you,\n{{organization_name}}"),
        ]
        for name, category, channel, subject, body in templates:
            MessageTemplate.objects.create(
                organization=org, name=name, category=category, channel=channel,
                subject=subject, body=body, is_active=True, is_default=True,
                created_by=owner, updated_by=owner,
            )
        self.stdout.write("  + 5 message templates")

    def _seed_subscription(self, org):
        from apps.subscriptions.models import Subscription, Plan
        plan = Plan.objects.get(name="growth")
        Subscription.objects.create(
            organization=org, plan=plan, status="active",
            billing_cycle="monthly",
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self.stdout.write("  + Active subscription (Growth plan)")

    def _seed_portal_users(self, org, customers):
        from apps.customer_portal.models import PortalUser
        from django.contrib.auth.hashers import make_password
        for i, c in enumerate(customers[:5], 1):
            PortalUser.objects.create(
                organization=org, customer=c,
                email=f"customer{i}@demo.com",
                password_hash=make_password("Demo@12345"),
                is_active=True, is_email_verified=True,
                created_by=users_first if (users_first := User.objects.filter(email="owner@demo.com").first()) else None,
                updated_by=users_first,
            )
        self.stdout.write("  + 5 customer portal users")

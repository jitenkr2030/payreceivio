# PayReceivio

**Universal Receivables & Payment Collection Platform**

> Collect Smarter. Get Paid Faster.

PayReceivio is a multi-tenant SaaS platform that helps businesses manage customer outstanding balances, automate payment follow-ups, collect payments, reconcile transactions and synchronise receipts with their existing accounting and ERP software.

## Tech Stack

- **Backend**: Django 5.x + Django REST Framework
- **Database**: PostgreSQL (SQLite for dev)
- **Frontend**: Bootstrap 5 + Django templates + HTMX + Chart.js
- **Async**: Celery + Redis
- **Auth**: Django auth + TOTP MFA (django-otp)
- **Tenancy**: Custom middleware (session-based active organization)
- **Container**: Docker + docker-compose

## Quick Start (local dev)

```bash
# 1. Create virtual env and install deps
python -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt

# 2. Create .env
cp .env.example .env
# Edit .env: set DJANGO_SECRET_KEY to a 50+ char random string

# 3. Run migrations
python manage.py migrate

# 4. Seed demo data (creates 1 org, 50 customers, 200 invoices, 80 payments, etc.)
python manage.py seed_data

# 5. Create superuser (optional)
python manage.py createsuperuser

# 6. Run server
python manage.py runserver
```

Open http://localhost:8000

## Default Demo Logins

After running `seed_data`:

| Role | Email | Password |
|------|-------|----------|
| Owner | owner@demo.com | Demo@12345 |
| Finance Manager | finance@demo.com | Demo@12345 |
| Accountant | accountant@demo.com | Demo@12345 |
| Collection Manager | collection_mgr@demo.com | Demo@12345 |
| Collection Executive | collections@demo.com | Demo@12345 |
| Sales Manager | sales_mgr@demo.com | Demo@12345 |
| Salesperson | sales@demo.com | Demo@12345 |
| Salesperson 2 | sales2@demo.com | Demo@12345 |
| Auditor | auditor@demo.com | Demo@12345 |
| Customer Portal | customer1@demo.com | Demo@12345 |

## Docker

```bash
docker-compose up -d
# Web at http://localhost:8000
# Postgres on 5432, Redis on 6379
# Celery worker + beat running in background
```

## Project Structure

```
payreceivio/
├── config/                    # settings, urls, celery
│   ├── settings/{base,dev,prod}.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/              # users, roles, MFA, auth
│   ├── tenants/               # multi-tenant middleware & mixins
│   ├── organizations/         # org, company, branch, department, territory
│   ├── audit/                 # audit log, approval requests
│   ├── integrations/          # universal connector framework
│   ├── tally_connector/       # TallyPrime XML/JSON connector
│   ├── zoho_connector/        # Zoho Books OAuth REST connector
│   ├── accounting_connectors/ # 17 more connectors (BUSY, Marg, QBO, Xero, Sage, D365, NetSuite, SAP B1, Odoo, MYOB, FreshBooks, Wave, GoFrugal, Focus, Exact, AutoCount, Money Forward)
│   ├── customers/             # customer master, contacts, ledger
│   ├── receivables/           # invoices, credit/debit notes, allocations
│   ├── payments/              # payments, links, transactions, refunds
│   ├── collections/           # tasks, follow-ups, promises, visits
│   ├── reconciliation/        # bank import, matching engine
│   ├── communications/        # templates, email/SMS/WhatsApp, campaigns
│   ├── workflows/             # rule engine, automation
│   ├── credit_management/     # limits, scoring, alerts
│   ├── analytics/             # dashboards, KPIs, reports
│   ├── customer_portal/       # customer self-service
│   ├── field_sales/           # salesperson portal
│   ├── disputes/              # payment disputes
│   ├── targets/               # collection targets
│   ├── documents/             # document management
│   ├── subscriptions/         # plans, trials, usage, billing
│   ├── ai_assistant/          # NL Q&A engine
│   ├── notifications/         # in-app notifications
│   └── administration/        # API tokens, settings, exports
├── templates/                 # base + per-module templates
├── static/                    # CSS, JS vendor
├── requirements/              # base.txt, dev.txt, prod.txt
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── README.md
```

## Module Coverage (16 modules)

1. **Connect** - Accounting integrations with **19 fully implemented connectors**: TallyPrime, Zoho Books, BUSY, Marg ERP, QuickBooks Online, Xero, Sage Business Cloud, Microsoft Dynamics 365 BC, Oracle NetSuite, SAP Business One, Odoo, MYOB, FreshBooks, Wave Financial, GoFrugal, Focus Softnet, Exact Online, AutoCount, Money Forward Cloud
2. **Receivables** - Invoices, credit/debit notes, ageing, due monitoring
3. **Collect** - Payments (UPI/NEFT/RTGS/IMPS/Cheque/Cash), links, receipts
4. **Engage** - WhatsApp, email, SMS automation with templates and campaigns
5. **Reconcile** - Bank statement CSV import, multi-pass matching engine
6. **Credit** - Credit limits, payment reliability scoring, alerts
7. **Intelligence** - 6 dashboards, 20 reports, KPIs (DSO, efficiency)
8. **Automate** - Workflow rule engine with trigger/condition/action
9. **Portal** - Customer self-service (invoices, pay, statements, requests)
10. **Sales** - Salesperson dashboard, visits, GPS check-in stub
11. **Documents** - Document storage, versioning, sharing
12. **Assistant** - AI collections Q&A (rule-based, extensible to LLM)
13. **Disputes** - Payment dispute registration and resolution
14. **Targets** - Collection targets and performance scorecards
15. **Admin** - Org config, API tokens, data exports, audit logs
16. **SaaS** - Subscription plans, trials, usage tracking, billing

## Key Features

- Multi-tenant with session-based org switching
- Role-based access (10 system roles + custom roles)
- TOTP MFA
- Audit log of every financial operation
- Idempotent payment processing (UTR-based deduplication)
- Multi-pass reconciliation engine (UTR exact, reference exact, amount+name, amount-only)
- Ageing buckets (Current, 1-30, 31-60, 61-90, 91-180, 180+)
- WhatsApp-first reminder schedule (configurable)
- AI assistant with cited sources (no external LLM cost)
- Customer portal + salesperson portal
- 19 fully implemented accounting vendor connectors (each with auth, fetch_customers, fetch_invoices, fetch_receipts, post_receipt, test_connection)
- Multi-tenant with session-based org switching

## API

REST API at `/api/` with JWT authentication. Browseable at `/api/auth/`.

Key endpoints:
- `/api/customers/` - Customer CRUD
- `/api/invoices/` - Invoice CRUD + allocate action
- `/api/payments/` - Payment CRUD
- `/api/bank-transactions/` - Bank transaction listing
- `/api/dashboard/metrics/` - Dashboard KPIs

## Tests

```bash
pytest
```

## Production Deployment

1. Set `DJANGO_SETTINGS_MODULE=config.settings.prod`
2. Set secure `DJANGO_SECRET_KEY`
3. Set `DJANGO_ALLOWED_HOSTS` to your domain
4. Configure PostgreSQL via `DATABASE_URL`
5. Configure Redis for Celery
6. Set up SMTP email
7. Configure S3 for file storage (`USE_S3=True`)
8. Run `python manage.py collectstatic`
9. Run with gunicorn: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`

## License

Proprietary. Copyright PayReceivio.

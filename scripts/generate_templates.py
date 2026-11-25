#!/usr/bin/env python3
"""Generate all remaining PayReceivio templates in one pass."""
import os
from pathlib import Path

BASE = Path("/home/z/my-project/payreceivio/templates")

# (relative_path, content) pairs
TEMPLATES = {
    "receivables/invoice_list.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
    <h1><i class="bi bi-receipt"></i> Invoices</h1>
    <div>
        <a href="{% url 'receivables:invoice_overdue' %}" class="btn btn-outline-danger btn-sm">Overdue</a>
        <a href="{% url 'receivables:invoice_due_today' %}" class="btn btn-outline-warning btn-sm">Due Today</a>
        <a href="{% url 'receivables:invoice_upcoming' %}" class="btn btn-outline-info btn-sm">Upcoming</a>
        <a href="{% url 'receivables:invoice_create' %}" class="btn btn-primary"><i class="bi bi-plus-lg"></i> New Invoice</a>
    </div>
</div>

<div class="row g-2 mb-3">
    <div class="col-md-2"><strong>Ageing:</strong></div>
    {% for bucket, label in AGEING_BUCKETS %}
    <div class="col-md-1 small">{{ label }}: <br><strong>{{ CURRENCY_SYMBOL }}{{ ageing_summary|lookup:bucket|floatformat:0|intcomma }}</strong></div>
    {% endfor %}
    <div class="col-md-1 small">Total: <br><strong>{{ CURRENCY_SYMBOL }}{{ ageing_summary.total|floatformat:0|intcomma }}</strong></div>
</div>

<form method="get" class="row g-2 mb-3">
    <div class="col-md-5"><input type="text" name="q" value="{{ q }}" class="form-control" placeholder="Search invoice # or customer..."></div>
    <div class="col-md-3"><select name="status" class="form-select">
        <option value="">All status</option>
        <option value="unpaid" {% if status == 'unpaid' %}selected{% endif %}>Unpaid</option>
        <option value="partially_paid" {% if status == 'partially_paid' %}selected{% endif %}>Partially Paid</option>
        <option value="paid" {% if status == 'paid' %}selected{% endif %}>Paid</option>
        <option value="overdue" {% if status == 'overdue' %}selected{% endif %}>Overdue</option>
        <option value="cancelled" {% if status == 'cancelled' %}selected{% endif %}>Cancelled</option>
    </select></div>
    <div class="col-md-2"><button class="btn btn-outline-primary">Search</button></div>
</form>

<div class="card"><div class="card-body">
<table class="table table-hover table-sm">
<thead><tr><th>Invoice #</th><th>Customer</th><th>Date</th><th>Due</th><th class="text-end">Total</th><th class="text-end">Outstanding</th><th>Status</th></tr></thead>
<tbody>
{% for i in invoices %}
<tr>
    <td><a href="{% url 'receivables:invoice_detail' i.pk %}">{{ i.invoice_number }}</a></td>
    <td>{{ i.customer.name }}</td>
    <td>{{ i.invoice_date|date:"d M Y" }}</td>
    <td>{{ i.due_date|date:"d M Y" }}{% if i.status == 'overdue' %} <span class="badge bg-danger">Overdue</span>{% endif %}</td>
    <td class="text-end">{{ CURRENCY_SYMBOL }}{{ i.total_amount|floatformat:0|intcomma }}</td>
    <td class="text-end">{{ CURRENCY_SYMBOL }}{{ i.outstanding_amount|floatformat:0|intcomma }}</td>
    <td><span class="badge bg-{% if i.status == 'paid' %}success{% elif i.status == 'overdue' %}danger{% elif i.status == 'partially_paid' %}warning{% else %}info{% endif %}">{{ i.get_status_display }}</span></td>
</tr>
{% empty %}
<tr><td colspan="7" class="text-center text-muted py-3">No invoices</td></tr>
{% endfor %}
</tbody>
</table>
</div></div>
{% if is_paginated %}
<nav><ul class="pagination">
{% if page_obj.has_previous %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Prev</a></li>{% endif %}
<li class="page-item active"><a class="page-link">{{ page_obj.number }} / {{ paginator.num_pages }}</a></li>
{% if page_obj.has_next %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a></li>{% endif %}
</ul></nav>
{% endif %}
{% endblock %}
""",
    "receivables/invoice_detail.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
    <h1><i class="bi bi-receipt"></i> Invoice {{ invoice.invoice_number }}</h1>
    <div>
        <a href="{% url 'receivables:invoice_update' invoice.pk %}" class="btn btn-outline-primary">Edit</a>
        {% if invoice.outstanding_amount > 0 %}<a href="{% url 'payments:create' %}?customer={{ invoice.customer_id }}" class="btn btn-success">Record Payment</a>{% endif %}
    </div>
</div>

<div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card text-white bg-primary"><div class="card-body">
        <div class="small">Total Amount</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ invoice.total_amount|floatformat:2|intcomma }}</div>
    </div></div></div>
    <div class="col-md-3"><div class="card text-white bg-success"><div class="card-body">
        <div class="small">Paid</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ invoice.paid_amount|floatformat:2|intcomma }}</div>
    </div></div></div>
    <div class="col-md-3"><div class="card text-white bg-danger"><div class="card-body">
        <div class="small">Outstanding</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ invoice.outstanding_amount|floatformat:2|intcomma }}</div>
    </div></div></div>
    <div class="col-md-3"><div class="card"><div class="card-body">
        <div class="small text-muted">Status</div><div class="h3"><span class="badge bg-{% if invoice.status == 'paid' %}success{% elif invoice.status == 'overdue' %}danger{% elif invoice.status == 'partially_paid' %}warning{% else %}info{% endif %}">{{ invoice.get_status_display }}</span></div>
    </div></div></div>
</div>

<div class="row g-4">
    <div class="col-md-6">
        <div class="card h-100"><div class="card-header">Invoice Details</div><div class="card-body">
            <table class="table table-sm">
                <tr><th>Customer</th><td><a href="{% url 'customers:detail' invoice.customer_id %}">{{ invoice.customer.name }}</a></td></tr>
                <tr><th>Invoice Date</th><td>{{ invoice.invoice_date|date:"d M Y" }}</td></tr>
                <tr><th>Due Date</th><td>{{ invoice.due_date|date:"d M Y" }}</td></tr>
                <tr><th>Subtotal</th><td>{{ CURRENCY_SYMBOL }}{{ invoice.subtotal|floatformat:2 }}</td></tr>
                <tr><th>Tax</th><td>{{ CURRENCY_SYMBOL }}{{ invoice.tax_amount|floatformat:2 }}</td></tr>
                <tr><th>Adjustment</th><td>{{ CURRENCY_SYMBOL }}{{ invoice.adjustment|floatformat:2 }}</td></tr>
                <tr><th>Payment Terms</th><td>{{ invoice.payment_terms }}</td></tr>
                <tr><th>Salesperson</th><td>{{ invoice.salesperson.display_name|default:"-" }}</td></tr>
                <tr><th>Accounting Ref</th><td>{{ invoice.accounting_ref|default:"Not synced" }}</td></tr>
            </table>
            {% if invoice.notes %}<div class="alert alert-info"><strong>Notes:</strong> {{ invoice.notes }}</div>{% endif %}
        </div></div>
    </div>
    <div class="col-md-6">
        <div class="card h-100"><div class="card-header">Payment Allocations</div><div class="card-body">
            <table class="table table-sm">
                <thead><tr><th>Date</th><th>Receipt #</th><th>Method</th><th class="text-end">Amount</th></tr></thead>
                <tbody>
                    {% for a in allocations %}
                    <tr>
                        <td>{{ a.payment.payment_date|date:"d M Y" }}</td>
                        <td><a href="{% url 'payments:detail' a.payment_id %}">{{ a.payment.payment_number }}</a></td>
                        <td>{{ a.payment.get_payment_method_display }}</td>
                        <td class="text-end">{{ CURRENCY_SYMBOL }}{{ a.amount|floatformat:2|intcomma }}</td>
                    </tr>
                    {% empty %}
                    <tr><td colspan="4" class="text-center text-muted">No payments allocated yet</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div></div>
    </div>
</div>
{% endblock %}
""",
    "receivables/invoice_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>{% if form.instance.pk %}Edit Invoice{% else %}New Invoice{% endif %}</h1>
<form method="post">{% csrf_token %}
<div class="row g-3">
    <div class="col-md-3"><label class="form-label">Invoice Number</label>{{ form.invoice_number }}</div>
    <div class="col-md-5"><label class="form-label">Customer</label>{{ form.customer }}</div>
    <div class="col-md-2"><label class="form-label">Invoice Date</label>{{ form.invoice_date }}</div>
    <div class="col-md-2"><label class="form-label">Due Date</label>{{ form.due_date }}</div>
    <div class="col-md-3"><label class="form-label">Subtotal</label>{{ form.subtotal }}</div>
    <div class="col-md-3"><label class="form-label">Tax</label>{{ form.tax_amount }}</div>
    <div class="col-md-3"><label class="form-label">Adjustment</label>{{ form.adjustment }}</div>
    <div class="col-md-3"><label class="form-label">Currency</label>{{ form.currency }}</div>
    <div class="col-md-4"><label class="form-label">Salesperson</label>{{ form.salesperson }}</div>
    <div class="col-md-4"><label class="form-label">Status</label>{{ form.status }}</div>
    <div class="col-md-4"><label class="form-label">Payment Terms</label>{{ form.payment_terms }}</div>
    <div class="col-md-12"><label class="form-label">Notes</label>{{ form.notes }}</div>
</div>
<button class="btn btn-primary mt-3">Save</button>
<a href="{% url 'receivables:invoice_list' %}" class="btn btn-outline-secondary mt-3">Cancel</a>
</form>
{% endblock %}
""",
    "receivables/invoice_overdue.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<h1><i class="bi bi-exclamation-triangle text-danger"></i> Overdue Invoices</h1>
<table class="table table-hover">
<thead><tr><th>Invoice #</th><th>Customer</th><th>Due Date</th><th class="text-end">Outstanding</th><th>Days Overdue</th></tr></thead>
<tbody>
{% for i in invoices %}
<tr class="table-danger">
    <td><a href="{% url 'receivables:invoice_detail' i.pk %}">{{ i.invoice_number }}</a></td>
    <td>{{ i.customer.name }}</td>
    <td>{{ i.due_date|date:"d M Y" }}</td>
    <td class="text-end">{{ CURRENCY_SYMBOL }}{{ i.outstanding_amount|floatformat:0|intcomma }}</td>
    <td><span class="badge bg-danger">{{ today|default:''|truncatechars:0 }}{# compute in view #}</span></td>
</tr>
{% empty %}
<tr><td colspan="5" class="text-center text-success py-4">No overdue invoices!</td></tr>
{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "receivables/invoice_due_today.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<h1><i class="bi bi-calendar-day text-warning"></i> Due Today</h1>
<table class="table">
<thead><tr><th>Invoice #</th><th>Customer</th><th class="text-end">Outstanding</th></tr></thead>
<tbody>
{% for i in invoices %}
<tr><td><a href="{% url 'receivables:invoice_detail' i.pk %}">{{ i.invoice_number }}</a></td><td>{{ i.customer.name }}</td><td class="text-end">{{ CURRENCY_SYMBOL }}{{ i.outstanding_amount|floatformat:2|intcomma }}</td></tr>
{% empty %}<tr><td colspan="3" class="text-center text-muted">None due today</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "receivables/invoice_upcoming.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<h1><i class="bi bi-calendar-week text-info"></i> Upcoming Receivables (7 days)</h1>
<table class="table">
<thead><tr><th>Invoice #</th><th>Customer</th><th>Due Date</th><th class="text-end">Outstanding</th></tr></thead>
<tbody>
{% for i in invoices %}
<tr><td><a href="{% url 'receivables:invoice_detail' i.pk %}">{{ i.invoice_number }}</a></td><td>{{ i.customer.name }}</td><td>{{ i.due_date|date:"d M Y" }}</td><td class="text-end">{{ CURRENCY_SYMBOL }}{{ i.outstanding_amount|floatformat:2|intcomma }}</td></tr>
{% empty %}<tr><td colspan="4" class="text-center text-muted">None upcoming</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "receivables/creditnote_list.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<h1>Credit Notes</h1>
<a href="{% url 'receivables:creditnote_create' %}" class="btn btn-primary mb-3">New Credit Note</a>
<table class="table">
<thead><tr><th>CN #</th><th>Customer</th><th>Date</th><th class="text-end">Amount</th><th>Adjusted</th></tr></thead>
<tbody>
{% for c in credit_notes %}
<tr><td>{{ c.credit_note_number }}</td><td>{{ c.customer.name }}</td><td>{{ c.date }}</td><td class="text-end">{{ CURRENCY_SYMBOL }}{{ c.amount|floatformat:0|intcomma }}</td><td>{% if c.is_adjusted %}<span class="badge bg-success">Yes</span>{% else %}<span class="badge bg-warning">No</span>{% endif %}</td></tr>
{% empty %}<tr><td colspan="5" class="text-center text-muted">No credit notes</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "receivables/creditnote_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>New Credit Note</h1>
<form method="post">{% csrf_token %}
{{ form.as_p }}
<button class="btn btn-primary">Save</button>
</form>
{% endblock %}
""",
    "receivables/debitnote_list.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Debit Notes</h1>
<a href="{% url 'receivables:debitnote_create' %}" class="btn btn-primary mb-3">New Debit Note</a>
<table class="table">
<thead><tr><th>DN #</th><th>Customer</th><th>Date</th><th class="text-end">Amount</th></tr></thead>
<tbody>
{% for d in debit_notes %}<tr><td>{{ d.debit_note_number }}</td><td>{{ d.customer.name }}</td><td>{{ d.date }}</td><td class="text-end">{{ d.amount }}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No debit notes</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "receivables/debitnote_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>New Debit Note</h1>
<form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Save</button></form>
{% endblock %}
""",

    "payments/payment_list.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
    <h1><i class="bi bi-credit-card"></i> Payments</h1>
    <div>
        <a href="{% url 'payments:link_create' %}" class="btn btn-outline-primary">Generate Payment Link</a>
        <a href="{% url 'payments:create' %}" class="btn btn-success"><i class="bi bi-plus-lg"></i> Record Payment</a>
    </div>
</div>
<form method="get" class="row g-2 mb-3">
    <div class="col-md-5"><input name="q" value="{{ q }}" class="form-control" placeholder="Search reference or customer..."></div>
    <div class="col-md-3"><select name="status" class="form-select">
        <option value="">All status</option>
        <option value="confirmed" {% if status == 'confirmed' %}selected{% endif %}>Confirmed</option>
        <option value="pending" {% if status == 'pending' %}selected{% endif %}>Pending</option>
        <option value="failed" {% if status == 'failed' %}selected{% endif %}>Failed</option>
    </select></div>
    <div class="col-md-3"><select name="method" class="form-select">
        <option value="">All methods</option>
        <option value="upi" {% if method == 'upi' %}selected{% endif %}>UPI</option>
        <option value="neft" {% if method == 'neft' %}selected{% endif %}>NEFT</option>
        <option value="rtgs" {% if method == 'rtgs' %}selected{% endif %}>RTGS</option>
        <option value="cheque" {% if method == 'cheque' %}selected{% endif %}>Cheque</option>
        <option value="cash" {% if method == 'cash' %}selected{% endif %}>Cash</option>
    </select></div>
    <div class="col-md-1"><button class="btn btn-outline-primary">Go</button></div>
</form>
<div class="card"><div class="card-body">
<table class="table table-hover">
<thead><tr><th>Receipt #</th><th>Customer</th><th>Date</th><th>Method</th><th>Reference</th><th class="text-end">Amount</th><th>Status</th><th>Reconciled</th></tr></thead>
<tbody>
{% for p in payments %}
<tr>
    <td><a href="{% url 'payments:detail' p.pk %}">{{ p.payment_number }}</a></td>
    <td>{{ p.customer.name }}</td>
    <td>{{ p.payment_date|date:"d M Y" }}</td>
    <td><span class="badge bg-secondary">{{ p.get_payment_method_display }}</span></td>
    <td>{{ p.reference|default:"-" }}</td>
    <td class="text-end">{{ CURRENCY_SYMBOL }}{{ p.amount|floatformat:2|intcomma }}</td>
    <td><span class="badge bg-{% if p.status == 'confirmed' %}success{% elif p.status == 'failed' %}danger{% else %}warning{% endif %}">{{ p.get_status_display }}</span></td>
    <td>{% if p.is_reconciled %}<i class="bi bi-check-circle text-success"></i>{% else %}<i class="bi bi-circle text-muted"></i>{% endif %}</td>
</tr>
{% empty %}<tr><td colspan="8" class="text-center text-muted py-3">No payments</td></tr>{% endfor %}
</tbody>
</table>
</div></div>
{% if is_paginated %}<nav><ul class="pagination">
{% if page_obj.has_previous %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Prev</a></li>{% endif %}
<li class="page-item active"><a class="page-link">{{ page_obj.number }} / {{ paginator.num_pages }}</a></li>
{% if page_obj.has_next %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a></li>{% endif %}
</ul></nav>{% endif %}
{% endblock %}
""",
    "payments/payment_detail.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
    <h1><i class="bi bi-credit-card"></i> Payment {{ payment.payment_number }}</h1>
    {% if payment.unallocated_amount > 0 %}<a href="{% url 'payments:allocate' payment.pk %}" class="btn btn-warning">Allocate to Invoices</a>{% endif %}
</div>
<div class="row g-3 mb-4">
    <div class="col-md-4"><div class="card text-white bg-success"><div class="card-body">
        <div class="small">Amount</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ payment.amount|floatformat:2|intcomma }}</div>
    </div></div></div>
    <div class="col-md-4"><div class="card text-white bg-primary"><div class="card-body">
        <div class="small">Allocated</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ payment.allocated_amount|floatformat:2|intcomma }}</div>
    </div></div></div>
    <div class="col-md-4"><div class="card text-white {% if payment.unallocated_amount > 0 %}bg-warning{% else %}bg-info{% endif %}"><div class="card-body">
        <div class="small">Unallocated</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ payment.unallocated_amount|floatformat:2|intcomma }}</div>
    </div></div></div>
</div>
<div class="card"><div class="card-header">Payment Details</div><div class="card-body">
<table class="table">
<tr><th>Customer</th><td><a href="{% url 'customers:detail' payment.customer_id %}">{{ payment.customer.name }}</a></td></tr>
<tr><th>Date</th><td>{{ payment.payment_date|date:"d M Y" }}</td></tr>
<tr><th>Method</th><td>{{ payment.get_payment_method_display }}</td></tr>
<tr><th>Type</th><td>{{ payment.get_payment_type_display }}</td></tr>
<tr><th>Reference</th><td>{{ payment.reference|default:"-" }}</td></tr>
<tr><th>Bank</th><td>{{ payment.bank_name|default:"-" }}</td></tr>
<tr><th>Cheque Number</th><td>{{ payment.cheque_number|default:"-" }}</td></tr>
<tr><th>Receipt Number</th><td>{{ payment.receipt_number|default:"-" }}</td></tr>
<tr><th>Status</th><td><span class="badge bg-{% if payment.status == 'confirmed' %}success{% elif p.status == 'failed' %}danger{% else %}warning{% endif %}">{{ payment.get_status_display }}</span></td></tr>
<tr><th>Reconciled</th><td>{% if payment.is_reconciled %}Yes (with bank txn {{ payment.reconciled_with_id }}){% else %}No{% endif %}</td></tr>
<tr><th>Accounting Sync</th><td>{% if payment.is_synced %}Synced ({{ payment.accounting_ref }}){% else %}Not synced{% endif %}</td></tr>
</table>
</div></div>
<div class="card mt-3"><div class="card-header">Invoice Allocations</div><div class="card-body">
<table class="table table-sm">
<thead><tr><th>Invoice #</th><th class="text-end">Amount Allocated</th><th>Allocated By</th></tr></thead>
<tbody>
{% for a in allocations %}<tr><td><a href="{% url 'receivables:invoice_detail' a.invoice_id %}">{{ a.invoice.invoice_number }}</a></td><td class="text-end">{{ CURRENCY_SYMBOL }}{{ a.amount|floatformat:2|intcomma }}</td><td>{{ a.allocated_by.display_name|default:"-" }}</td></tr>{% empty %}<tr><td colspan="3" class="text-center text-muted">No allocations</td></tr>{% endfor %}
</tbody>
</table>
</div></div>
{% endblock %}
""",
    "payments/payment_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Record Payment</h1>
<form method="post">{% csrf_token %}
<div class="row g-3">
    <div class="col-md-6"><label class="form-label">Customer</label>{{ form.customer }}</div>
    <div class="col-md-3"><label class="form-label">Payment Date</label>{{ form.payment_date }}</div>
    <div class="col-md-3"><label class="form-label">Amount</label>{{ form.amount }}</div>
    <div class="col-md-4"><label class="form-label">Method</label>{{ form.payment_method }}</div>
    <div class="col-md-4"><label class="form-label">Type</label>{{ form.payment_type }}</div>
    <div class="col-md-4"><label class="form-label">Reference (UTR/Cheque)</label>{{ form.reference }}</div>
    <div class="col-md-4"><label class="form-label">Bank Name</label>{{ form.bank_name }}</div>
    <div class="col-md-4"><label class="form-label">Cheque Number</label>{{ form.cheque_number }}</div>
    <div class="col-md-4"><label class="form-label">Cheque Date</label>{{ form.cheque_date }}</div>
    <div class="col-md-12"><label class="form-label">Notes</label>{{ form.notes }}</div>
</div>
<button class="btn btn-success mt-3">Record Payment</button>
<a href="{% url 'payments:list' %}" class="btn btn-outline-secondary mt-3">Cancel</a>
</form>
{% endblock %}
""",
    "payments/payment_allocate.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<h1>Allocate Payment {{ payment.payment_number }}</h1>
<p>Customer: {{ payment.customer.name }} | Unallocated: {{ CURRENCY_SYMBOL }}{{ payment.unallocated_amount|floatformat:2|intcomma }}</p>
<form method="post">{% csrf_token %}
<table class="table">
<thead><tr><th>Invoice #</th><th>Due Date</th><th class="text-end">Outstanding</th><th class="text-end">Allocate</th></tr></thead>
<tbody>
{% for field in form %}
{% if field.name|slice:":8" == "invoice_" %}
<tr><td>{{ field.label }}</td><td></td><td></td><td>{{ field }}</td></tr>
{% endif %}
{% endfor %}
</tbody>
</table>
<button class="btn btn-primary">Allocate</button>
</form>
{% endblock %}
""",
    "payments/link_list.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Payment Links</h1>
<a href="{% url 'payments:link_create' %}" class="btn btn-primary mb-3">New Link</a>
<table class="table">
<thead><tr><th>Link ID</th><th>Customer</th><th class="text-end">Amount</th><th>Status</th><th>URL</th></tr></thead>
<tbody>
{% for l in links %}
<tr><td>{{ l.link_id|truncatechars:20 }}</td><td>{{ l.customer.name }}</td><td class="text-end">{{ l.amount }}</td><td><span class="badge bg-{% if l.status == 'paid' %}success{% elif l.status == 'active' %}primary{% else %}secondary{% endif %}">{{ l.status }}</span></td><td><a href="{{ l.short_url }}" target="_blank">{{ l.short_url|truncatechars:30 }}</a></td></tr>
{% empty %}<tr><td colspan="5" class="text-center text-muted">No payment links</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "payments/link_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Generate Payment Link</h1>
<form method="post">{% csrf_token %}
{{ form.as_p }}
<button class="btn btn-primary">Generate</button>
</form>
{% endblock %}
""",
    "payments/refund_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Refunds</h1><table class="table"><tr><th>Refund #</th><th>Payment</th><th>Amount</th><th>Status</th></tr>{% for r in refunds %}<tr><td>{{ r.refund_number }}</td><td>{{ r.payment_id }}</td><td>{{ r.amount }}</td><td>{{ r.status }}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No refunds</td></tr>{% endfor %}</table>{% endblock %}
""",

    "collections/task_list.html": """{% extends "base/base.html" %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
    <h1><i class="bi bi-list-check"></i> Collection Tasks</h1>
    <a href="{% url 'collections:task_create' %}" class="btn btn-primary"><i class="bi bi-plus-lg"></i> New Task</a>
</div>
<form method="get" class="mb-3"><select name="status" class="form-select" style="max-width:200px" onchange="this.form.submit()">
    <option value="">All status</option>
    <option value="open" {% if status == 'open' %}selected{% endif %}>Open</option>
    <option value="in_progress" {% if status == 'in_progress' %}selected{% endif %}>In Progress</option>
    <option value="completed" {% if status == 'completed' %}selected{% endif %}>Completed</option>
    <option value="overdue" {% if status == 'overdue' %}selected{% endif %}>Overdue</option>
</select></form>
<div class="card"><div class="card-body">
<table class="table table-hover">
<thead><tr><th>Title</th><th>Customer</th><th>Type</th><th>Priority</th><th>Assigned To</th><th>Due</th><th>Status</th></tr></thead>
<tbody>
{% for t in tasks %}
<tr class="{% if t.status == 'overdue' %}table-danger{% endif %}">
    <td>{{ t.title }}</td>
    <td><a href="{% url 'customers:detail' t.customer_id %}">{{ t.customer.name }}</a></td>
    <td>{{ t.get_task_type_display }}</td>
    <td><span class="badge bg-{% if t.priority == 'urgent' %}danger{% elif t.priority == 'high' %}warning{% else %}info{% endif %}">{{ t.get_priority_display }}</span></td>
    <td>{{ t.assigned_to.display_name }}</td>
    <td>{{ t.due_date|date:"d M Y" }}</td>
    <td><span class="badge bg-{% if t.status == 'completed' %}success{% elif t.status == 'overdue' %}danger{% elif t.status == 'in_progress' %}warning{% else %}primary{% endif %}">{{ t.get_status_display }}</span></td>
</tr>
{% empty %}<tr><td colspan="7" class="text-center text-muted py-3">No tasks</td></tr>{% endfor %}
</tbody>
</table>
</div></div>
{% endblock %}
""",
    "collections/task_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>New Collection Task</h1>
<form method="post">{% csrf_token %}
{{ form.as_p }}
<button class="btn btn-primary">Create Task</button>
</form>
{% endblock %}
""",
    "collections/followup_list.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Follow-ups</h1>
<a href="{% url 'collections:followup_create' %}" class="btn btn-primary mb-3">Log Follow-up</a>
<table class="table">
<thead><tr><th>Date</th><th>Customer</th><th>Channel</th><th>Outcome</th><th>By</th></tr></thead>
<tbody>
{% for f in followups %}
<tr><td>{{ f.followup_at|date:"d M Y H:i" }}</td><td>{{ f.customer.name }}</td><td>{{ f.get_channel_display }}</td><td>{{ f.get_outcome_display }}</td><td>{{ f.followed_up_by.display_name|default:"-" }}</td></tr>
{% empty %}<tr><td colspan="5" class="text-center text-muted">No follow-ups</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "collections/followup_form.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Log Follow-up</h1>
<form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Save</button></form>
{% endblock %}
""",
    "collections/promise_list.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Promises to Pay</h1>
<a href="{% url 'collections:promise_create' %}" class="btn btn-primary mb-3">New Promise</a>
<table class="table">
<thead><tr><th>Customer</th><th>Amount</th><th>Promised Date</th><th>Status</th></tr></thead>
<tbody>
{% for p in promises %}
<tr><td>{{ p.customer.name }}</td><td>{{ p.amount }}</td><td>{{ p.promised_date }}</td><td><span class="badge bg-{% if p.status == 'fulfilled' %}success{% elif p.status == 'broken' %}danger{% else %}warning{% endif %}">{{ p.status }}</span></td></tr>
{% empty %}<tr><td colspan="4" class="text-center text-muted">No promises</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "collections/promise_form.html": """{% extends "base/base.html" %}
{% block content %}<h1>New Promise to Pay</h1><form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Save</button></form>{% endblock %}
""",
    "collections/visit_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Field Visits</h1><table class="table"><tr><th>Customer</th><th>Salesperson</th><th>Planned</th><th>Checked In</th><th>Status</th></tr>{% for v in visits %}<tr><td>{{ v.customer.name }}</td><td>{{ v.salesperson.display_name|default:'-' }}</td><td>{{ v.planned_at }}</td><td>{{ v.checked_in_at }}</td><td>{{ v.status }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No visits</td></tr>{% endfor %}</table>{% endblock %}
""",

    "reconciliation/bank_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Bank Accounts</h1><table class="table"><tr><th>Account Name</th><th>Bank</th><th>Account #</th><th>IFSC</th></tr>{% for b in bank_accounts %}<tr><td>{{ b.account_name }}</td><td>{{ b.bank_name }}</td><td>{{ b.account_number }}</td><td>{{ b.ifsc_code }}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No bank accounts</td></tr>{% endfor %}</table>{% endblock %}
""",
    "reconciliation/statement_list.html": """{% extends "base/base.html" %}
{% block content %}
<div class="d-flex justify-content-between mb-3"><h1>Bank Statements</h1>
<a href="{% url 'reconciliation:statement_new' %}" class="btn btn-primary">Import Statement</a></div>
<table class="table">
<thead><tr><th>Date</th><th>Bank Account</th><th class="text-end">Credits</th><th class="text-end">Debits</th><th>Txns</th><th>Matched</th><th>Status</th></tr></thead>
<tbody>
{% for s in statements %}<tr>
    <td>{{ s.statement_date }}</td><td>{{ s.bank_account.account_name }}</td>
    <td class="text-end">{{ s.total_credits }}</td><td class="text-end">{{ s.total_debits }}</td>
    <td>{{ s.transaction_count }}</td><td>{{ s.matched_count }}</td>
    <td>{% if s.is_fully_processed %}<span class="badge bg-success">Complete</span>{% else %}<span class="badge bg-warning">In Progress</span>{% endif %}</td>
</tr>{% empty %}<tr><td colspan="7" class="text-center text-muted">No statements</td></tr>{% endfor %}
</tbody>
</table>
{% endblock %}
""",
    "reconciliation/import.html": """{% extends "base/base.html" %}
{% block content %}<h1>New Bank Statement</h1><form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Create & Upload</button></form>{% endblock %}
""",
    "reconciliation/upload.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Upload Transactions</h1>
<p>Statement for {{ statement.bank_account.account_name }} on {{ statement.statement_date }}</p>
<form method="post" enctype="multipart/form-data">{% csrf_token %}
    <input type="file" name="file" accept=".csv" class="form-control mb-3" required>
    <p class="text-muted small">CSV columns: date, amount, type, description, reference, utr, counterparty</p>
    <button class="btn btn-primary">Upload & Auto-Match</button>
</form>
{% endblock %}
""",
    "reconciliation/unmatched_list.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}
<h1><i class="bi bi-search"></i> Unmatched Bank Transactions</h1>
<table class="table table-hover">
<thead><tr><th>Date</th><th>Description</th><th>Reference</th><th>UTR</th><th class="text-end">Amount</th><th>Status</th><th>Actions</th></tr></thead>
<tbody>
{% for t in transactions %}
<tr class="{% if t.status == 'suggested' %}table-warning{% endif %}">
    <td>{{ t.transaction_date|date:"d M Y" }}</td>
    <td>{{ t.description|truncatechars:50 }}</td>
    <td>{{ t.reference_number|default:"-" }}</td>
    <td>{{ t.utr_number|default:"-" }}</td>
    <td class="text-end">{{ CURRENCY_SYMBOL }}{{ t.amount|floatformat:2|intcomma }}</td>
    <td><span class="badge bg-{% if t.status == 'suggested' %}warning{% else %}secondary{% endif %}">{{ t.get_status_display }}</span></td>
    <td>
        <a href="{% url 'reconciliation:match' t.pk %}" class="btn btn-sm btn-outline-primary">Match</a>
        <form method="post" action="{% url 'reconciliation:ignore' t.pk %}" class="d-inline">{% csrf_token %}<button class="btn btn-sm btn-outline-secondary">Ignore</button></form>
    </td>
</tr>
{% empty %}<tr><td colspan="7" class="text-center text-success py-3">All transactions matched!</td></tr>{% endfor %}
</tbody>
</table>
{% if is_paginated %}<nav><ul class="pagination">
{% if page_obj.has_previous %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Prev</a></li>{% endif %}
<li class="page-item active"><a class="page-link">{{ page_obj.number }} / {{ paginator.num_pages }}</a></li>
{% if page_obj.has_next %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a></li>{% endif %}
</ul></nav>{% endif %}
{% endblock %}
""",
    "reconciliation/match_suggestions.html": """{% extends "base/base.html" %}
{% block content %}
<h1>Match Bank Transaction</h1>
<div class="card mb-3"><div class="card-body">
<p><strong>Date:</strong> {{ txn.transaction_date }}</p>
<p><strong>Amount:</strong> {{ txn.amount }}</p>
<p><strong>Description:</strong> {{ txn.description }}</p>
<p><strong>UTR:</strong> {{ txn.utr_number|default:"-" }}</p>
</div></div>
<h3>Suggested Payments</h3>
<form method="post">{% csrf_token %}
<table class="table">
<thead><tr><th>Receipt #</th><th>Customer</th><th>Date</th><th class="text-end">Amount</th><th>Action</th></tr></thead>
<tbody>
{% for p in candidates %}
<tr><td>{{ p.payment_number }}</td><td>{{ p.customer.name }}</td><td>{{ p.payment_date }}</td><td class="text-end">{{ p.amount }}</td><td><button type="submit" name="payment_id" value="{{ p.id }}" class="btn btn-sm btn-success">Approve Match</button></td></tr>
{% empty %}<tr><td colspan="5" class="text-center text-muted">No matching payments found</td></tr>{% endfor %}
</tbody>
</table>
</form>
{% endblock %}
""",
    "reconciliation/match_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Reconciliation Matches</h1><table class="table"><tr><th>Bank Txn</th><th>Payment</th><th>Type</th><th>Confidence</th><th>Approved</th></tr>{% for m in matches %}<tr><td>{{ m.bank_transaction_id }}</td><td>{{ m.payment_id }}</td><td>{{ m.match_type }}</td><td>{{ m.confidence }}%</td><td>{{ m.approved_at|default:"Pending" }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No matches</td></tr>{% endfor %}</table>{% endblock %}
""",

    "communications/template_list.html": """{% extends "base/base.html" %}
{% block content %}<div class="d-flex justify-content-between mb-3"><h1>Message Templates</h1><a href="{% url 'communications:template_create' %}" class="btn btn-primary">New Template</a></div>
<table class="table"><tr><th>Name</th><th>Channel</th><th>Category</th><th>Active</th></tr>{% for t in templates %}<tr><td>{{ t.name }}</td><td><span class="badge bg-secondary">{{ t.get_channel_display }}</span></td><td>{{ t.get_category_display }}</td><td>{% if t.is_active %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No templates</td></tr>{% endfor %}</table>{% endblock %}
""",
    "communications/template_form.html": """{% extends "base/base.html" %}
{% block content %}<h1>New Message Template</h1><form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Save</button></form>{% endblock %}
""",
    "communications/message_list.html": """{% extends "base/base.html" %}
{% block content %}<div class="d-flex justify-content-between mb-3"><h1>Messages</h1><a href="{% url 'communications:compose' %}" class="btn btn-primary">Compose</a></div>
<table class="table"><tr><th>Customer</th><th>Channel</th><th>Subject</th><th>Status</th><th>Sent At</th><th></th></tr>{% for m in messages %}<tr><td>{{ m.customer.name|default:'-' }}</td><td><span class="badge bg-secondary">{{ m.get_channel_display }}</span></td><td>{{ m.subject|truncatechars:40 }}</td><td><span class="badge bg-{% if m.status == 'sent' or m.status == 'delivered' %}success{% elif m.status == 'failed' %}danger{% else %}warning{% endif %}">{{ m.get_status_display }}</span></td><td>{{ m.sent_at|default:'-' }}</td><td><a href="{% url 'communications:message_detail' m.pk %}" class="btn btn-sm btn-outline-primary">View</a></td></tr>{% empty %}<tr><td colspan="6" class="text-center text-muted">No messages</td></tr>{% endfor %}</table>{% endblock %}
""",
    "communications/message_detail.html": """{% extends "base/base.html" %}
{% block content %}<h1>Message</h1>
<div class="card mb-3"><div class="card-body">
<p><strong>To:</strong> {{ message.to_address }}</p>
<p><strong>Subject:</strong> {{ message.subject }}</p>
<p><strong>Channel:</strong> {{ message.get_channel_display }}</p>
<p><strong>Status:</strong> {{ message.get_status_display }}</p>
{% if message.status == 'queued' %}<form method="post" action="{% url 'communications:message_send' message.pk %}">{% csrf_token %}<button class="btn btn-primary">Send Now</button></form>{% endif %}
</div></div>
<div class="card"><div class="card-header">Body</div><div class="card-body"><pre>{{ message.body }}</pre></div></div>
{% endblock %}
""",
    "communications/compose.html": """{% extends "base/base.html" %}
{% block content %}<h1>Compose Message</h1>
<form method="post">{% csrf_token %}
<div class="row g-3">
    <div class="col-md-6"><label>Customer</label><select name="customer" class="form-select" required>{% for c in customers %}<option value="{{ c.id }}">{{ c.name }} ({{ c.code }})</option>{% endfor %}</select></div>
    <div class="col-md-3"><label>Template</label><select name="template" class="form-select"><option value="">None</option>{% for t in templates %}<option value="{{ t.id }}">{{ t.name }} ({{ t.get_channel_display }})</option>{% endfor %}</select></div>
    <div class="col-md-3"><label>Channel</label><select name="channel" class="form-select"><option value="email">Email</option><option value="sms">SMS</option><option value="whatsapp">WhatsApp</option></select></div>
    <div class="col-md-12"><label>Subject</label><input name="subject" class="form-control"></div>
    <div class="col-md-12"><label>Body</label><textarea name="body" class="form-control" rows="8"></textarea></div>
</div>
<button class="btn btn-primary mt-3">Send</button>
</form>
{% endblock %}
""",
    "communications/campaign_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Campaigns</h1><table class="table"><tr><th>Name</th><th>Channel</th><th>Status</th><th>Sent</th></tr>{% for c in campaigns %}<tr><td>{{ c.name }}</td><td>{{ c.get_channel_display }}</td><td>{{ c.get_status_display }}</td><td>{{ c.sent_count }}/{{ c.total_recipients }}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No campaigns</td></tr>{% endfor %}</table>{% endblock %}
""",

    "credit/assessment_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Credit Assessments</h1><table class="table"><tr><th>Customer</th><th>Date</th><th>Score</th><th>Risk</th><th>Outstanding</th><th>Overdue</th></tr>{% for a in assessments %}<tr><td>{{ a.customer.name }}</td><td>{{ a.assessment_date }}</td><td>{{ a.payment_reliability_score }}</td><td><span class="badge bg-{% if a.risk_category == 'low' %}success{% elif a.risk_category == 'medium' %}warning{% else %}danger{% endif %}">{{ a.get_risk_category_display }}</span></td><td>{{ a.outstanding_amount }}</td><td>{{ a.overdue_amount }}</td></tr>{% empty %}<tr><td colspan="6" class="text-center text-muted">No assessments</td></tr>{% endfor %}</table>{% endblock %}
""",
    "credit/alert_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Credit Alerts</h1><table class="table"><tr><th>Customer</th><th>Type</th><th>Severity</th><th>Message</th><th>Date</th></tr>{% for a in alerts %}<tr class="{% if a.severity == 'critical' %}table-danger{% elif a.severity == 'warning' %}table-warning{% endif %}"><td>{{ a.customer.name }}</td><td>{{ a.get_alert_type_display }}</td><td><span class="badge bg-{% if a.severity == 'critical' %}danger{% elif a.severity == 'warning' %}warning{% else %}info{% endif %}">{{ a.severity }}</span></td><td>{{ a.message }}</td><td>{{ a.created_at|date:"d M Y" }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No alerts</td></tr>{% endfor %}</table>{% endblock %}
""",

    "analytics/dashboard_finance.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}<h1>Finance Manager Dashboard</h1>
<div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card text-white bg-primary"><div class="card-body"><div class="small">Total Receivables</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ kpis.total_receivables|floatformat:0|intcomma }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-danger"><div class="card-body"><div class="small">Overdue</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ kpis.total_overdue|floatformat:0|intcomma }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-success"><div class="card-body"><div class="small">Collected (Month)</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ kpis.collected_this_month|floatformat:0|intcomma }}</div></div></div></div>
    <div class="col-md-3"><div class="card"><div class="card-body"><div class="small">DSO</div><div class="h3">{{ kpis.dso|floatformat:1 }} days</div></div></div></div>
</div>
<div class="card"><div class="card-header">Ageing Summary</div><div class="card-body">
<table class="table">{% for bucket, label in AGEING_BUCKETS %}<tr><td>{{ label }}</td><td class="text-end">{{ CURRENCY_SYMBOL }}{{ kpis.ageing_summary|lookup:bucket|floatformat:2|intcomma }}</td></tr>{% endfor %}<tr class="table-dark"><td><strong>Total</strong></td><td class="text-end"><strong>{{ CURRENCY_SYMBOL }}{{ kpis.ageing_summary.total|floatformat:2|intcomma }}</strong></td></tr></table>
</div></div>
{% endblock %}
""",
    "analytics/dashboard_collection.html": """{% extends "base/base.html" %}
{% block content %}<h1>Collection Team Dashboard</h1>
<div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card text-white bg-primary"><div class="card-body"><div class="small">Open Tasks</div><div class="h3">{{ open_tasks }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-danger"><div class="card-body"><div class="small">Overdue Tasks</div><div class="h3">{{ overdue_tasks }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-warning"><div class="card-body"><div class="small">Total Overdue Receivables</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ kpis.total_overdue|floatformat:0 }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-info"><div class="card-body"><div class="small">Overdue Customers</div><div class="h3">{{ kpis.overdue_customer_count }}</div></div></div></div>
</div>
<a href="{% url 'collections:task_list' %}" class="btn btn-primary">View Tasks</a>
<a href="{% url 'reconciliation:unmatched' %}" class="btn btn-outline-primary">Reconcile Payments</a>
{% endblock %}
""",

    "portal/login.html": """{% extends "base/base.html" %}
{% block content %}<div class="row justify-content-center mt-5"><div class="col-md-5"><div class="card"><div class="card-body p-4">
<h3 class="text-center">Customer Portal Login</h3>
<form method="post">{% csrf_token %}
<div class="mb-3"><label>Email</label><input type="email" name="email" class="form-control" required></div>
<div class="mb-3"><label>Password</label><input type="password" name="password" class="form-control" required></div>
<button class="btn btn-primary w-100">Login</button>
</form>
</div></div></div></div>
{% endblock %}
""",
    "portal/dashboard.html": """{% extends "base/base.html" %}
{% load humanize %}
{% block content %}<h1>Welcome, {{ customer.name }}</h1>
<div class="row g-3 mb-4">
    <div class="col-md-4"><div class="card text-white bg-primary"><div class="card-body"><div class="small">Outstanding Balance</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ customer.outstanding_balance|floatformat:2|intcomma }}</div></div></div></div>
    <div class="col-md-4"><div class="card"><div class="card-body"><div class="small text-muted">Credit Limit</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ customer.credit_limit|floatformat:0|intcomma }}</div></div></div></div>
    <div class="col-md-4"><div class="card"><div class="card-body"><div class="small text-muted">Risk Category</div><div class="h3"><span class="badge bg-{% if customer.risk_category == 'low' %}success{% elif customer.risk_category == 'medium' %}warning{% else %}danger{% endif %}">{{ customer.get_risk_category_display }}</span></div></div></div></div>
</div>
<h3>Outstanding Invoices</h3>
<table class="table"><tr><th>Invoice #</th><th>Date</th><th>Due</th><th class="text-end">Outstanding</th><th></th></tr>
{% for i in invoices %}<tr><td>{{ i.invoice_number }}</td><td>{{ i.invoice_date|date:"d M Y" }}</td><td>{{ i.due_date|date:"d M Y" }}</td><td class="text-end">{{ CURRENCY_SYMBOL }}{{ i.outstanding_amount|floatformat:2|intcomma }}</td><td><a href="{% url 'portal:invoice_detail' i.pk %}" class="btn btn-sm btn-outline-primary">View</a> <a href="{% url 'portal:pay_now' i.pk %}" class="btn btn-sm btn-success">Pay Now</a></td></tr>{% empty %}<tr><td colspan="5" class="text-center text-success">No outstanding invoices!</td></tr>{% endfor %}
</table>
<div class="mt-3"><a href="{% url 'portal:invoices' %}" class="btn btn-outline-primary">All Invoices</a> <a href="{% url 'portal:statement' %}" class="btn btn-outline-secondary">Statement</a> <a href="{% url 'portal:payments' %}" class="btn btn-outline-secondary">Payment History</a> <a href="{% url 'portal:raise_request' %}" class="btn btn-outline-warning">Raise Request</a></div>
{% endblock %}
""",
    "portal/invoice_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Your Invoices</h1>
<table class="table"><tr><th>Invoice #</th><th>Date</th><th>Due</th><th class="text-end">Total</th><th class="text-end">Outstanding</th><th>Status</th><th></th></tr>
{% for i in invoices %}<tr><td>{{ i.invoice_number }}</td><td>{{ i.invoice_date|date:"d M Y" }}</td><td>{{ i.due_date|date:"d M Y" }}</td><td class="text-end">{{ i.total_amount }}</td><td class="text-end">{{ i.outstanding_amount }}</td><td><span class="badge bg-{% if i.status == 'paid' %}success{% elif i.status == 'overdue' %}danger{% else %}info{% endif %}">{{ i.get_status_display }}</span></td><td><a href="{% url 'portal:invoice_detail' i.pk %}" class="btn btn-sm btn-outline-primary">View</a></td></tr>{% endfor %}
</table>
{% endblock %}
""",
    "portal/invoice_detail.html": """{% extends "base/base.html" %}
{% block content %}<h1>Invoice {{ invoice.invoice_number }}</h1>
<div class="card mb-3"><div class="card-body">
<p><strong>Date:</strong> {{ invoice.invoice_date }}</p>
<p><strong>Due:</strong> {{ invoice.due_date }}</p>
<p><strong>Total:</strong> {{ invoice.total_amount }}</p>
<p><strong>Outstanding:</strong> {{ invoice.outstanding_amount }}</p>
{% if invoice.outstanding_amount > 0 %}<a href="{% url 'portal:pay_now' invoice.pk %}" class="btn btn-success">Pay Now</a>{% endif %}
</div></div>
{% endblock %}
""",
    "portal/statement.html": """{% extends "base/base.html" %}
{% block content %}<h1>Account Statement</h1>
<p><strong>Opening Balance:</strong> {{ opening_balance }}</p>
<table class="table"><tr><th>Date</th><th>Type</th><th>Reference</th><th class="text-end">Debit</th><th class="text-end">Credit</th><th class="text-end">Balance</th></tr>
{% for e in entries %}<tr><td>{{ e.date }}</td><td>{{ e.type }}</td><td>{{ e.reference }}</td><td class="text-end">{{ e.debit|default:'-' }}</td><td class="text-end">{{ e.credit|default:'-' }}</td><td class="text-end">{{ e.balance }}</td></tr>{% endfor %}
</table>
<p><strong>Closing Balance:</strong> {{ closing_balance }}</p>
{% endblock %}
""",
    "portal/payment_history.html": """{% extends "base/base.html" %}
{% block content %}<h1>Payment History</h1>
<table class="table"><tr><th>Date</th><th>Receipt #</th><th>Method</th><th class="text-end">Amount</th></tr>
{% for p in payments %}<tr><td>{{ p.payment_date }}</td><td>{{ p.payment_number }}</td><td>{{ p.get_payment_method_display }}</td><td class="text-end">{{ p.amount }}</td></tr>{% endfor %}
</table>
{% endblock %}
""",
    "portal/raise_request.html": """{% extends "base/base.html" %}
{% block content %}<h1>Raise a Request</h1>
<form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Submit</button></form>
{% endblock %}
""",

    "sales/dashboard.html": """{% extends "base/base.html" %}
{% block content %}<h1>Salesperson Dashboard</h1>
<div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card text-white bg-success"><div class="card-body"><div class="small">Collected Today</div><div class="h3">{{ CURRENCY_SYMBOL }}{{ collected_today|floatformat:0 }}</div></div></div></div>
    <div class="col-md-3"><div class="card"><div class="card-body"><div class="small text-muted">My Customers</div><div class="h3">{{ customers|length }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-primary"><div class="card-body"><div class="small">Open Tasks</div><div class="h3">{{ open_tasks|length }}</div></div></div></div>
    <div class="col-md-3"><div class="card text-white bg-warning"><div class="card-body"><div class="small">Today's Visits</div><div class="h3">{{ today_visits|length }}</div></div></div></div>
</div>
<h3>Open Tasks</h3><table class="table"><tr><th>Task</th><th>Customer</th><th>Due</th></tr>{% for t in open_tasks %}<tr><td>{{ t.title }}</td><td>{{ t.customer.name }}</td><td>{{ t.due_date }}</td></tr>{% empty %}<tr><td colspan="3" class="text-center text-muted">No open tasks</td></tr>{% endfor %}</table>
<h3>My Customers</h3><table class="table"><tr><th>Name</th><th>Code</th><th>Outstanding</th></tr>{% for c in customers %}<tr><td>{{ c.name }}</td><td>{{ c.code }}</td><td>{{ c.outstanding_balance }}</td></tr>{% endfor %}</table>
{% endblock %}
""",

    "disputes/dispute_list.html": """{% extends "base/base.html" %}
{% block content %}<div class="d-flex justify-content-between mb-3"><h1>Disputes</h1><a href="{% url 'disputes:create' %}" class="btn btn-primary">New Dispute</a></div>
<table class="table"><tr><th>Dispute #</th><th>Customer</th><th>Type</th><th class="text-end">Amount</th><th>Status</th></tr>
{% for d in disputes %}<tr><td><a href="{% url 'disputes:detail' d.pk %}">{{ d.dispute_number }}</a></td><td>{{ d.customer.name }}</td><td>{{ d.get_dispute_type_display }}</td><td class="text-end">{{ d.amount_in_dispute }}</td><td><span class="badge bg-{% if d.status == 'resolved' %}success{% elif d.status == 'open' %}warning{% else %}secondary{% endif %}">{{ d.get_status_display }}</span></td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No disputes</td></tr>{% endfor %}
</table>
{% endblock %}
""",
    "disputes/dispute_form.html": """{% extends "base/base.html" %}
{% block content %}<h1>New Dispute</h1><form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Save</button></form>{% endblock %}
""",
    "disputes/dispute_detail.html": """{% extends "base/base.html" %}
{% block content %}<h1>Dispute {{ dispute.dispute_number }}</h1>
<p><strong>Customer:</strong> {{ dispute.customer.name }}</p>
<p><strong>Type:</strong> {{ dispute.get_dispute_type_display }}</p>
<p><strong>Amount:</strong> {{ dispute.amount_in_dispute }}</p>
<p><strong>Status:</strong> {{ dispute.get_status_display }}</p>
<p><strong>Description:</strong> {{ dispute.description }}</p>
{% endblock %}
""",

    "targets/target_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Collection Targets</h1><table class="table"><tr><th>Name</th><th>Period</th><th>Scope</th><th class="text-end">Target</th><th class="text-end">Achieved</th><th>%</th></tr>{% for t in targets %}<tr><td>{{ t.name }}</td><td>{{ t.get_period_display }}</td><td>{{ t.get_scope_display }}</td><td class="text-end">{{ t.target_amount }}</td><td class="text-end">{{ t.achieved_amount }}</td><td>{% widthratio t.achieved_amount t.target_amount 100 %}%</td></tr>{% empty %}<tr><td colspan="6" class="text-center text-muted">No targets</td></tr>{% endfor %}</table>{% endblock %}
""",
    "documents/document_list.html": """{% extends "base/base.html" %}
{% block content %}<div class="d-flex justify-content-between mb-3"><h1>Documents</h1><a href="{% url 'documents:create' %}" class="btn btn-primary">Upload</a></div>
<table class="table"><tr><th>Name</th><th>Type</th><th>Customer</th><th>Shared</th><th>Created</th></tr>{% for d in documents %}<tr><td><a href="{% url 'documents:detail' d.pk %}">{{ d.name }}</a></td><td>{{ d.get_doc_type_display }}</td><td>{{ d.customer.name|default:'-' }}</td><td>{% if d.is_shared %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td><td>{{ d.created_at|date:"d M Y" }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No documents</td></tr>{% endfor %}</table>
{% endblock %}
""",
    "documents/document_form.html": """{% extends "base/base.html" %}
{% block content %}<h1>Upload Document</h1><form method="post" enctype="multipart/form-data">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Upload</button></form>{% endblock %}
""",
    "documents/document_detail.html": """{% extends "base/base.html" %}
{% block content %}<h1>{{ document.name }}</h1><p>Type: {{ document.get_doc_type_display }}</p><p>Customer: {{ document.customer.name|default:'-' }}</p>{% if document.file %}<a href="{{ document.file.url }}" class="btn btn-primary">Download</a>{% endif %}{% endblock %}
""",

    "subscriptions/plan_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Subscription Plans</h1>
<div class="row g-3">{% for p in plans %}
<div class="col-md-4"><div class="card h-100"><div class="card-body text-center">
<h4>{{ p.label }}</h4>{% if p.is_trial %}<span class="badge bg-info">Trial</span>{% endif %}
<div class="display-6 my-3">{% if p.monthly_price == 0 %}Free{% else %}{{ CURRENCY_SYMBOL }}{{ p.monthly_price }}<small class="text-muted">/mo</small>{% endif %}</div>
<ul class="list-unstyled small text-start">
<li>{{ p.max_companies }} companies</li><li>{{ p.max_branches }} branches</li>
<li>{{ p.max_users }} users</li><li>{{ p.max_invoices_per_month }} invoices/mo</li>
<li>{{ p.max_messages_per_month }} messages/mo</li>
<li>{{ p.max_accounting_connections }} accounting connections</li>
</ul>
</div></div></div>{% endfor %}</div>
{% endblock %}
""",
    "subscriptions/subscription_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Your Subscription</h1>
{% for s in subscriptions %}
<div class="card mb-3"><div class="card-body">
<h4>{{ s.plan.label }}</h4>
<p>Status: <span class="badge bg-{% if s.status == 'active' %}success{% elif s.status == 'trial' %}info{% else %}danger{% endif %}">{{ s.get_status_display }}</span></p>
<p>Billing: {{ s.get_billing_cycle_display }}</p>
<p>Started: {{ s.started_at|date:"d M Y" }}</p>
{% if s.current_period_end %}<p>Renews: {{ s.current_period_end|date:"d M Y" }}</p>{% endif %}
</div></div>
{% empty %}<div class="alert alert-info">No active subscription.</div>{% endfor %}
{% endblock %}
""",
    "subscriptions/billing_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Billing History</h1>
<table class="table"><tr><th>Invoice #</th><th>Date</th><th class="text-end">Amount</th><th>Status</th></tr>{% for i in invoices %}<tr><td>{{ i.invoice_number }}</td><td>{{ i.invoice_date }}</td><td class="text-end">{{ i.total_amount }}</td><td>{{ i.status }}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No invoices</td></tr>{% endfor %}</table>
{% endblock %}
""",

    "ai/chat.html": """{% extends "base/base.html" %}
{% block content %}
<div class="row">
    <div class="col-md-8">
        <h1><i class="bi bi-robot"></i> AI Collections Assistant</h1>
        <p class="text-muted">Ask questions about your receivables in natural language.</p>
        <div class="card mb-3" style="max-height:500px;overflow-y:auto">
            <div class="card-body">
                {% for m in messages %}
                <div class="mb-3 {% if m.role == 'user' %}text-end{% endif %}">
                    <span class="badge bg-{% if m.role == 'user' %}primary{% else %}secondary{% endif %}">{{ m.role|title }}</span>
                    <div class="alert {% if m.role == 'user' %}alert-primary{% else %}alert-light{% endif %} mt-1">{{ m.content|linebreaksbr }}</div>
                </div>
                {% empty %}
                <div class="text-center text-muted py-4">
                    <i class="bi bi-robot" style="font-size:3rem"></i>
                    <p>Ask me anything about your receivables.</p>
                </div>
                {% endfor %}
            </div>
        </div>
        <form method="post">{% csrf_token %}
            <div class="input-group">
                <input type="text" name="question" class="form-control" placeholder="Ask a question..." required>
                <button class="btn btn-primary" type="submit"><i class="bi bi-send"></i> Ask</button>
            </div>
        </form>
    </div>
    <div class="col-md-4">
        <h5>Suggested Questions</h5>
        <div class="list-group">
            {% for q in suggested_questions %}
            <form method="post" class="list-group-item list-group-item-action">{% csrf_token %}
                <input type="hidden" name="question" value="{{ q }}">
                <button type="submit" class="btn btn-link text-start p-0">{{ q }}</button>
            </form>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
""",

    "notifications/list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Notifications</h1>
<table class="table"><tr><th>Type</th><th>Title</th><th>Message</th><th>Date</th><th></th></tr>
{% for n in notifications %}
<tr class="{% if not n.is_read %}table-primary{% endif %}">
<td><span class="badge bg-secondary">{{ n.get_notif_type_display }}</span></td><td>{{ n.title }}</td><td>{{ n.message|truncatechars:80 }}</td><td>{{ n.created_at|date:"d M Y H:i" }}</td>
<td>{% if not n.is_read %}<button onclick="markRead({{ n.pk }})" class="btn btn-sm btn-outline-primary">Mark Read</button>{% endif %}</td>
</tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No notifications</td></tr>{% endfor %}
</table>
<script>
function markRead(id){fetch('/notifications/'+id+'/read/',{method:'POST',headers:{'X-CSRFToken':'{{ csrf_token }}'}}).then(()=>location.reload())}
</script>
{% endblock %}
""",

    "admin/home.html": """{% extends "base/base.html" %}
{% block content %}<h1>Administration</h1>
<div class="row g-3">
<div class="col-md-4"><div class="card"><div class="card-body"><h5>API Tokens</h5><a href="{% url 'administration:api_tokens' %}" class="btn btn-outline-primary">Manage</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-body"><h5>Data Exports</h5><a href="{% url 'administration:exports' %}" class="btn btn-outline-primary">View</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-body"><h5>Audit Logs</h5><a href="{% url 'audit:logs' %}" class="btn btn-outline-primary">View</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-body"><h5>Users & Roles</h5><a href="{% url 'organizations:role_list' %}" class="btn btn-outline-primary">Manage</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-body"><h5>Integrations</h5><a href="{% url 'integrations:connection_list' %}" class="btn btn-outline-primary">Manage</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-body"><h5>Subscription</h5><a href="{% url 'subscriptions:list' %}" class="btn btn-outline-primary">View</a></div></div></div>
</div>
{% endblock %}
""",
    "admin/api_tokens.html": """{% extends "base/base.html" %}
{% block content %}<h1>API Tokens</h1><table class="table"><tr><th>Name</th><th>Token</th><th>Last Used</th><th>Active</th></tr>{% for t in tokens %}<tr><td>{{ t.name }}</td><td><code>{{ t.token }}</code></td><td>{{ t.last_used_at|default:'-' }}</td><td>{% if t.is_active %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No tokens</td></tr>{% endfor %}</table>{% endblock %}
""",
    "admin/data_exports.html": """{% extends "base/base.html" %}
{% block content %}<h1>Data Exports</h1><table class="table"><tr><th>Type</th><th>Status</th><th>Date</th></tr>{% for e in exports %}<tr><td>{{ e.export_type }}</td><td>{{ e.status }}</td><td>{{ e.created_at }}</td></tr>{% empty %}<tr><td colspan="3" class="text-center text-muted">No exports</td></tr>{% endfor %}</table>{% endblock %}
""",

    "audit/audit_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Audit Logs</h1>
<table class="table"><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>IP</th></tr>
{% for log in logs %}<tr><td>{{ log.created_at|date:"d M Y H:i" }}</td><td>{{ log.user.display_name|default:'-' }}</td><td>{{ log.action }}</td><td>{{ log.entity_type }}:{{ log.entity_id }}</td><td>{{ log.ip_address }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No audit logs</td></tr>{% endfor %}
</table>
{% if is_paginated %}<nav><ul class="pagination">{% if page_obj.has_previous %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}">Prev</a></li>{% endif %}<li class="page-item active"><a class="page-link">{{ page_obj.number }} / {{ paginator.num_pages }}</a></li>{% if page_obj.has_next %}<li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a></li>{% endif %}</ul></nav>{% endif %}
{% endblock %}
""",

    "workflows/workflow_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Workflows</h1><table class="table"><tr><th>Name</th><th>Trigger</th><th>Active</th><th>Executions</th><th>Last Run</th></tr>{% for w in workflows %}<tr><td>{{ w.name }}</td><td>{{ w.get_trigger_event_display }}</td><td>{% if w.is_active %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td><td>{{ w.total_executions }}</td><td>{{ w.last_run_at|default:'Never' }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No workflows</td></tr>{% endfor %}</table>{% endblock %}
""",

    "integrations/connector_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Accounting Connectors</h1>
<div class="row g-3">{% for c in connectors %}
<div class="col-md-4"><div class="card"><div class="card-body"><h5>{{ c.label }}</h5><p class="text-muted">{{ c.vendor }}</p><p><span class="badge bg-secondary">{{ c.auth_method }}</span> {% if c.is_active %}<span class="badge bg-success">Active</span>{% endif %}</p></div></div></div>
{% endfor %}</div>
{% endblock %}
""",
    "integrations/connection_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Accounting Connections</h1>
<table class="table"><tr><th>Name</th><th>Connector</th><th>Company</th><th>Status</th><th>Last Sync</th></tr>
{% for c in connections %}<tr><td>{{ c.name }}</td><td>{{ c.connector.label }}</td><td>{{ c.company.name }}</td><td><span class="badge bg-{% if c.status == 'active' %}success{% elif c.status == 'error' %}danger{% else %}warning{% endif %}">{{ c.get_status_display }}</span></td><td>{{ c.last_sync_at|default:'Never' }}</td></tr>{% empty %}<tr><td colspan="5" class="text-center text-muted">No connections</td></tr>{% endfor %}
</table>
{% endblock %}
""",
    "integrations/sync_job_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Sync Jobs</h1>
<table class="table"><tr><th>Connection</th><th>Direction</th><th>Status</th><th>Processed</th><th>Started</th><th>Completed</th></tr>
{% for j in jobs %}<tr><td>{{ j.connection.name }}</td><td>{{ j.direction }}</td><td><span class="badge bg-{% if j.status == 'completed' %}success{% elif j.status == 'failed' %}danger{% else %}warning{% endif %}">{{ j.status }}</span></td><td>{{ j.records_processed }}</td><td>{{ j.started_at|date:"d M Y H:i" }}</td><td>{{ j.completed_at|date:"d M Y H:i" }}</td></tr>{% empty %}<tr><td colspan="6" class="text-center text-muted">No sync jobs</td></tr>{% endfor %}
</table>
{% endblock %}
""",

    "tally/docs.html": """{% extends "base/base.html" %}
{% block content %}<h1>TallyPrime Connector Documentation</h1>
<div class="card"><div class="card-body">
<h5>Setup</h5><p>The TallyPrime connector uses XML over HTTP via a local agent that proxies requests from PayReceivio cloud to the on-premise Tally installation.</p>
<h5 class="mt-3">Agent Installation</h5><p>Install the PayReceivio Tally Agent on the same Windows machine as TallyPrime. The agent connects to Tally's HTTP server (default port 9000) and exposes a secure API for PayReceivio cloud.</p>
<h5 class="mt-3">Supported Entities</h5><ul><li>Customers (Sundry Debtors ledgers)</li><li>Sales invoices (outstanding bills)</li><li>Credit notes</li><li>Receipt vouchers</li><li>Ledger balances</li></ul>
<h5 class="mt-3">Receipt Write-Back</h5><p>Approved receipts are posted to Tally as Receipt vouchers with bill-wise allocation. The XML format is generated by the connector and posted via the agent.</p>
</div></div>
{% endblock %}
""",
    "zoho/docs.html": """{% extends "base/base.html" %}
{% block content %}<h1>Zoho Books Connector Documentation</h1>
<div class="card"><div class="card-body">
<h5>Setup</h5><p>The Zoho Books connector uses REST API v3 with OAuth 2.0 authentication.</p>
<h5 class="mt-3">OAuth Flow</h5><ol><li>Create a Zoho API client at <a href="https://api-console.zoho.com">Zoho API Console</a></li><li>Configure the redirect URL to <code>{% url 'zoho:oauth_callback' %}</code></li><li>Authorize and obtain the refresh token</li><li>Store client_id, client_secret, and refresh_token in the connection credentials</li></ol>
<h5 class="mt-3">Data Center</h5><p>Supports .com, .in, .eu data centers. Set the data_center in the connection config.</p>
<h5 class="mt-3">Supported Entities</h5><ul><li>Contacts (customers)</li><li>Invoices</li><li>Credit notes</li><li>Customer payments (receipts)</li></ul>
</div></div>
{% endblock %}
""",

    "organizations/org_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Your Organizations</h1>
<table class="table"><tr><th>Name</th><th>Plan</th><th>Active</th></tr>{% for o in organizations %}<tr><td>{{ o.name }}</td><td>{{ o.subscription_plan }}</td><td>{% if o.is_active %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td></tr>{% empty %}<tr><td colspan="3" class="text-center text-muted">No organizations</td></tr>{% endfor %}</table>
{% endblock %}
""",
    "organizations/company_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Companies</h1><table class="table"><tr><th>Name</th><th>GST</th><th>Active</th></tr>{% for c in companies %}<tr><td>{{ c.name }}</td><td>{{ c.gst_number }}</td><td>{% if c.is_active %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td></tr>{% empty %}<tr><td colspan="3" class="text-center text-muted">No companies</td></tr>{% endfor %}</table>{% endblock %}
""",
    "organizations/branch_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Branches</h1><table class="table"><tr><th>Name</th><th>Company</th><th>Head Office</th></tr>{% for b in branches %}<tr><td>{{ b.name }}</td><td>{{ b.company.name }}</td><td>{% if b.is_head_office %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td></tr>{% empty %}<tr><td colspan="3" class="text-center text-muted">No branches</td></tr>{% endfor %}</table>{% endblock %}
""",
    "organizations/role_list.html": """{% extends "base/base.html" %}
{% block content %}<div class="d-flex justify-content-between mb-3"><h1>User Roles</h1><a href="{% url 'organizations:role_create' %}" class="btn btn-primary">Assign Role</a></div>
<table class="table"><tr><th>User</th><th>Role</th><th>Company</th><th>Active</th></tr>{% for a in assignments %}<tr><td>{{ a.user.display_name }}</td><td>{{ a.role.label }}</td><td>{{ a.company.name|default:'All' }}</td><td>{% if a.is_active %}<i class="bi bi-check-circle text-success"></i>{% endif %}</td></tr>{% empty %}<tr><td colspan="4" class="text-center text-muted">No roles assigned</td></tr>{% endfor %}</table>{% endblock %}
""",
    "organizations/role_form.html": """{% extends "base/base.html" %}
{% block content %}<h1>Assign Role</h1><form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn btn-primary">Assign</button></form>{% endblock %}
""",
    "organizations/department_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Departments</h1><table class="table"><tr><th>Name</th><th>Head</th></tr>{% for d in departments %}<tr><td>{{ d.name }}</td><td>{{ d.head.display_name|default:'-' }}</td></tr>{% empty %}<tr><td colspan="2" class="text-center text-muted">No departments</td></tr>{% endfor %}</table>{% endblock %}
""",
    "organizations/territory_list.html": """{% extends "base/base.html" %}
{% block content %}<h1>Territories</h1><table class="table"><tr><th>Name</th><th>Parent</th></tr>{% for t in territories %}<tr><td>{{ t.name }}</td><td>{{ t.parent.name|default:'-' }}</td></tr>{% empty %}<tr><td colspan="2" class="text-center text-muted">No territories</td></tr>{% endfor %}</table>{% endblock %}
""",
}

for path, content in TEMPLATES.items():
    full_path = BASE / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)
    print(f"Created: {path}")

print(f"\nTotal: {len(TEMPLATES)} templates created")

"""Receivables views."""
from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.tenants.mixins import TenantMixin

from .models import Invoice, CreditNote, DebitNote, InvoiceAllocation
from .forms import InvoiceForm, CreditNoteForm, DebitNoteForm
from .services import (
    update_invoice_status, get_overdue_invoices, get_invoices_due_today,
    get_upcoming_invoices, get_invoice_ageing_summary,
)


class InvoiceListView(TenantMixin, ListView):
    model = Invoice
    template_name = "receivables/invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        customer = self.request.GET.get("customer")
        if customer:
            qs = qs.filter(customer_id=customer)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(invoice_number__icontains=q) | qs.filter(customer__name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["ageing_summary"] = get_invoice_ageing_summary(self.request.active_organization)
        return ctx


class InvoiceDetailView(TenantMixin, DetailView):
    model = Invoice
    template_name = "receivables/invoice_detail.html"
    context_object_name = "invoice"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lines"] = self.object.lines.all()
        ctx["allocations"] = self.object.allocations.select_related("payment").all()
        ctx["credit_notes"] = self.object.credit_notes.all()
        return ctx


class InvoiceCreateView(TenantMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "receivables/invoice_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.active_organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        # Set company/branch if customer has them
        if form.instance.customer and form.instance.customer.company:
            form.instance.company = form.instance.customer.company
            form.instance.branch = form.instance.customer.branch
        # Compute total
        from decimal import Decimal
        form.instance.total_amount = (form.instance.subtotal or Decimal("0")) + \
                                     (form.instance.tax_amount or Decimal("0")) - \
                                     (form.instance.adjustment or Decimal("0"))
        form.instance.outstanding_amount = form.instance.total_amount
        messages.success(self.request, f"Invoice {form.instance.invoice_number} created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("receivables:invoice_detail", kwargs={"pk": self.object.pk})


class InvoiceUpdateView(TenantMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "receivables/invoice_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.active_organization
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        from decimal import Decimal
        form.instance.total_amount = (form.instance.subtotal or Decimal("0")) + \
                                     (form.instance.tax_amount or Decimal("0")) - \
                                     (form.instance.adjustment or Decimal("0"))
        form.instance.outstanding_amount = form.instance.total_amount - form.instance.paid_amount
        messages.success(self.request, f"Invoice {form.instance.invoice_number} updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("receivables:invoice_detail", kwargs={"pk": self.object.pk})


class OverdueInvoiceListView(TenantMixin, ListView):
    template_name = "receivables/invoice_overdue.html"
    context_object_name = "invoices"
    paginate_by = 25

    def get_queryset(self):
        return get_overdue_invoices(self.request.active_organization)


class DueTodayListView(TenantMixin, ListView):
    template_name = "receivables/invoice_due_today.html"
    context_object_name = "invoices"

    def get_queryset(self):
        return get_invoices_due_today(self.request.active_organization)


class UpcomingListView(TenantMixin, ListView):
    template_name = "receivables/invoice_upcoming.html"
    context_object_name = "invoices"

    def get_queryset(self):
        return get_upcoming_invoices(self.request.active_organization)


class CreditNoteListView(TenantMixin, ListView):
    model = CreditNote
    template_name = "receivables/creditnote_list.html"
    context_object_name = "credit_notes"


class CreditNoteCreateView(TenantMixin, CreateView):
    model = CreditNote
    form_class = CreditNoteForm
    template_name = "receivables/creditnote_form.html"
    success_url = reverse_lazy("receivables:creditnote_list")

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        messages.success(self.request, "Credit note created.")
        return super().form_valid(form)


class DebitNoteListView(TenantMixin, ListView):
    model = DebitNote
    template_name = "receivables/debitnote_list.html"
    context_object_name = "debit_notes"


class DebitNoteCreateView(TenantMixin, CreateView):
    model = DebitNote
    form_class = DebitNoteForm
    template_name = "receivables/debitnote_form.html"
    success_url = reverse_lazy("receivables:debitnote_list")

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        messages.success(self.request, "Debit note created.")
        return super().form_valid(form)

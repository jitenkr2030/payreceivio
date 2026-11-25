"""Customer views - list, detail, CRUD, statement, ledger."""
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from apps.tenants.mixins import TenantMixin
from apps.common.utils import format_currency

from .models import Customer, CustomerContact
from .forms import CustomerForm, CustomerContactForm, CustomerImportForm
from .services import (
    compute_customer_ageing, build_customer_statement, bulk_import_customers_from_csv
)


class CustomerListView(TenantMixin, ListView):
    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(code__icontains=q) | qs.filter(phone__icontains=q) | qs.filter(gst_number__icontains=q)
        salesperson = self.request.GET.get("salesperson")
        if salesperson:
            qs = qs.filter(salesperson_id=salesperson)
        risk = self.request.GET.get("risk")
        if risk:
            qs = qs.filter(risk_category=risk)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["risk"] = self.request.GET.get("risk", "")
        return ctx


class CustomerDetailView(TenantMixin, DetailView):
    model = Customer
    template_name = "customers/customer_detail.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customer = self.object
        ctx["ageing"] = compute_customer_ageing(customer)
        ctx["contacts"] = customer.contacts.all()
        ctx["invoices"] = customer.invoices.all()[:20]
        ctx["payments"] = customer.payments.all()[:20]
        ctx["ledger_entries"] = customer.ledger_entries.all()[:30]
        ctx["outstanding"] = customer.outstanding_balance
        return ctx


class CustomerCreateView(TenantMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Customer '{form.instance.name}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("customers:detail", kwargs={"pk": self.object.pk})


class CustomerUpdateView(TenantMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/customer_form.html"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Customer '{form.instance.name}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("customers:detail", kwargs={"pk": self.object.pk})


class CustomerStatementView(TenantMixin, View):
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk, organization=request.active_organization)
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        from datetime import datetime as dt
        try:
            from_date = dt.strptime(from_date, "%Y-%m-%d").date() if from_date else None
            to_date = dt.strptime(to_date, "%Y-%m-%d").date() if to_date else None
        except ValueError:
            from_date = to_date = None
        statement = build_customer_statement(customer, from_date, to_date)
        return render(request, "customers/customer_statement.html", statement)


class CustomerLedgerView(TenantMixin, View):
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk, organization=request.active_organization)
        entries = customer.ledger_entries.all()[:100]
        return render(request, "customers/customer_ledger.html", {"customer": customer, "entries": entries})


class CustomerImportView(LoginRequiredMixin, View):
    template_name = "customers/customer_import.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"form": CustomerImportForm()})

    def post(self, request, *args, **kwargs):
        form = CustomerImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        import csv
        from io import TextIOWrapper
        csv_file = TextIOWrapper(request.FILES["file"], encoding="utf-8")
        reader = csv.DictReader(csv_file)
        result = bulk_import_customers_from_csv(request.active_organization, list(reader))
        messages.success(
            request,
            f"Imported: {len(result['created'])} created, {len(result['updated'])} updated, {len(result['skipped'])} skipped."
        )
        return redirect("customers:list")

"""Customer portal views."""
from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView

from apps.customers.models import Customer
from apps.customers.services import build_customer_statement, compute_customer_ageing
from apps.receivables.models import Invoice
from apps.payments.services import create_payment_link

from .models import PortalUser, PortalRequest


def portal_login(request):
    """Simple email/password login for customer portal users."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        try:
            portal_user = PortalUser.objects.get(email=email, is_active=True)
            if check_password(password, portal_user.password_hash):
                request.session["portal_user_id"] = portal_user.id
                request.session["portal_customer_id"] = portal_user.customer_id
                messages.success(request, f"Welcome, {portal_user.customer.name}!")
                return redirect("portal:dashboard")
            messages.error(request, "Invalid credentials.")
        except PortalUser.DoesNotExist:
            messages.error(request, "Account not found.")
    return render(request, "portal/login.html")


def portal_logout(request):
    request.session.flush()
    messages.info(request, "Logged out.")
    return redirect("portal:login")


def portal_required(view_func):
    def wrapper(request, *args, **kwargs):
        portal_user_id = request.session.get("portal_user_id")
        if not portal_user_id:
            return redirect("portal:login")
        try:
            request.portal_user = PortalUser.objects.select_related("customer").get(pk=portal_user_id)
        except PortalUser.DoesNotExist:
            return redirect("portal:login")
        return view_func(request, *args, **kwargs)
    return wrapper


@portal_required
def dashboard(request):
    customer = request.portal_user.customer
    ageing = compute_customer_ageing(customer)
    invoices = customer.invoices.filter(outstanding_amount__gt=0).order_by("due_date")[:10]
    return render(request, "portal/dashboard.html",
                  {"customer": customer, "ageing": ageing, "invoices": invoices})


@portal_required
def invoice_list(request):
    customer = request.portal_user.customer
    invoices = customer.invoices.all().order_by("-invoice_date")
    return render(request, "portal/invoice_list.html",
                  {"customer": customer, "invoices": invoices})


@portal_required
def invoice_detail(request, pk):
    customer = request.portal_user.customer
    invoice = get_object_or_404(Invoice, pk=pk, customer=customer)
    return render(request, "portal/invoice_detail.html",
                  {"customer": customer, "invoice": invoice})


@portal_required
def pay_now(request, pk):
    """Generate a payment link for an invoice."""
    customer = request.portal_user.customer
    invoice = get_object_or_404(Invoice, pk=pk, customer=customer, outstanding_amount__gt=0)
    link = create_payment_link(
        organization=customer.organization, customer=customer,
        amount=invoice.outstanding_amount, invoice=invoice,
        description=f"Payment for {invoice.invoice_number}",
        created_by=None,
    )
    messages.success(request, f"Payment link created: {link.short_url}")
    return redirect("portal:invoice_detail", pk=pk)


@portal_required
def statement(request):
    customer = request.portal_user.customer
    stmt = build_customer_statement(customer)
    return render(request, "portal/statement.html", stmt)


@portal_required
def payment_history(request):
    customer = request.portal_user.customer
    payments = customer.payments.all().order_by("-payment_date")[:50]
    return render(request, "portal/payment_history.html",
                  {"customer": customer, "payments": payments})


class RaiseRequestForm(forms.ModelForm):
    class Meta:
        model = PortalRequest
        fields = ("request_type", "subject", "description")
        widgets = {
            "request_type": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


@portal_required
def raise_request(request):
    if request.method == "POST":
        form = RaiseRequestForm(request.POST)
        if form.is_valid():
            form.instance.customer = request.portal_user.customer
            form.instance.organization = request.portal_user.customer.organization
            form.save()
            messages.success(request, "Request submitted. Our team will get back to you.")
            return redirect("portal:dashboard")
    else:
        form = RaiseRequestForm()
    return render(request, "portal/raise_request.html", {"form": form})


app_name = "portal"
urlpatterns = [
    path("login/", portal_login, name="login"),
    path("logout/", portal_logout, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("invoices/", invoice_list, name="invoices"),
    path("invoices/<int:pk>/", invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/pay/", pay_now, name="pay_now"),
    path("statement/", statement, name="statement"),
    path("payments/", payment_history, name="payments"),
    path("raise-request/", raise_request, name="raise_request"),
]

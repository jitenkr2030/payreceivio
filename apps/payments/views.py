"""Payment views."""
from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View

from apps.tenants.mixins import TenantMixin

from .models import Payment, PaymentLink, Refund
from .forms import PaymentForm, AllocationForm, PaymentLinkForm
from .services import record_payment, allocate_payment, create_payment_link


class PaymentListView(TenantMixin, ListView):
    model = Payment
    template_name = "payments/payment_list.html"
    context_object_name = "payments"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        method = self.request.GET.get("method")
        if method:
            qs = qs.filter(payment_method=method)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(reference__icontains=q) | qs.filter(customer__name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status"] = self.request.GET.get("status", "")
        ctx["method"] = self.request.GET.get("method", "")
        return ctx


class PaymentDetailView(TenantMixin, DetailView):
    model = Payment
    template_name = "payments/payment_detail.html"
    context_object_name = "payment"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["allocations"] = self.object.allocations.select_related("invoice").all()
        ctx["transactions"] = self.object.transactions.all()
        ctx["refunds"] = self.object.refunds.all()
        return ctx


class PaymentCreateView(TenantMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = "payments/payment_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.active_organization
        return kwargs

    def form_valid(self, form):
        org = self.request.active_organization
        payment = record_payment(
            organization=org,
            customer=form.cleaned_data["customer"],
            amount=form.cleaned_data["amount"],
            payment_date=form.cleaned_data["payment_date"],
            payment_method=form.cleaned_data["payment_method"],
            payment_type=form.cleaned_data["payment_type"],
            reference=form.cleaned_data["reference"],
            received_by=self.request.user,
            notes=form.cleaned_data["notes"],
            request=self.request,
        )
        self.object = payment
        messages.success(self.request, f"Payment {payment.payment_number} recorded.")
        return redirect("payments:detail", pk=payment.pk)


class PaymentAllocateView(TenantMixin, View):
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, organization=request.active_organization)
        form = AllocationForm(payment=payment)
        return render(request, "payments/payment_allocate.html", {"payment": payment, "form": form})

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, organization=request.active_organization)
        form = AllocationForm(request.POST, payment=payment)
        allocations = []
        for name, value in request.POST.items():
            if name.startswith("invoice_") and value:
                invoice_id = name.replace("invoice_", "")
                allocations.append({"invoice_id": invoice_id, "amount": value})
        if allocations:
            allocate_payment(payment, allocations, user=request.user, request=request)
            messages.success(request, f"Allocated {len(allocations)} invoice(s).")
        return redirect("payments:detail", pk=payment.pk)


class PaymentLinkCreateView(TenantMixin, View):
    def get(self, request, *args, **kwargs):
        form = PaymentLinkForm(organization=request.active_organization)
        return render(request, "payments/link_form.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = PaymentLinkForm(request.POST, organization=request.active_organization)
        if not form.is_valid():
            return render(request, "payments/link_form.html", {"form": form})
        from apps.customers.models import Customer
        customer = Customer.objects.get(pk=form.cleaned_data["customer"], organization=request.active_organization)
        link = create_payment_link(
            organization=request.active_organization,
            customer=customer,
            amount=form.cleaned_data["amount"],
            description=form.cleaned_data["description"],
            expires_in_days=form.cleaned_data["expires_in_days"],
            created_by=request.user,
            request=request,
        )
        messages.success(request, f"Payment link created: {link.short_url}")
        return redirect("payments:link_list")


class PaymentLinkListView(TenantMixin, ListView):
    model = PaymentLink
    template_name = "payments/link_list.html"
    context_object_name = "links"


class RefundListView(TenantMixin, ListView):
    model = Refund
    template_name = "payments/refund_list.html"
    context_object_name = "refunds"

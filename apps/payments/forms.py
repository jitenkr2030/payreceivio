"""Payment forms."""
from django import forms

from .models import Payment, Refund


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("customer", "payment_date", "amount", "payment_method", "payment_type",
                  "reference", "bank_name", "cheque_number", "cheque_date", "notes")
        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "payment_type": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "cheque_number": forms.TextInput(attrs={"class": "form-control"}),
            "cheque_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            from apps.customers.models import Customer
            self.fields["customer"].queryset = Customer.objects.filter(organization=organization, is_active=True)


class AllocationForm(forms.Form):
    """Dynamic form for allocating a payment to multiple invoices."""
    def __init__(self, *args, payment=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment = payment
        if payment:
            from apps.receivables.models import Invoice
            invoices = Invoice.objects.filter(
                customer=payment.customer,
                outstanding_amount__gt=0,
                status__in=["unpaid", "partially_paid", "overdue"],
            )
            for inv in invoices:
                self.fields[f"invoice_{inv.pk}"] = forms.DecimalField(
                    label=f"{inv.invoice_number} (Outstanding: ₹{inv.outstanding_amount})",
                    required=False, min_value=0,
                    widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "max": str(inv.outstanding_amount)}),
                )


class PaymentLinkForm(forms.Form):
    customer = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-select"}))
    amount = forms.DecimalField(widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    expires_in_days = forms.IntegerField(initial=7, widget=forms.NumberInput(attrs={"class": "form-control"}))

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            from apps.customers.models import Customer
            self.fields["customer"].choices = [("", "—")] + [
                (c.pk, f"{c.name} ({c.code})") for c in Customer.objects.filter(organization=organization, is_active=True)
            ]

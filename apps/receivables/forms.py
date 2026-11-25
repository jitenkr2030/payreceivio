"""Receivables forms."""
from django import forms

from .models import Invoice, InvoiceLine, CreditNote, DebitNote


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ("invoice_number", "customer", "invoice_date", "due_date",
                  "subtotal", "tax_amount", "adjustment", "currency",
                  "payment_terms", "notes", "salesperson", "status")
        widgets = {
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "subtotal": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tax_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "adjustment": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "payment_terms": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "salesperson": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            from apps.customers.models import Customer
            self.fields["customer"].queryset = Customer.objects.filter(organization=organization, is_active=True)
            if not self.instance.pk:
                from .services import generate_invoice_number
                self.fields["invoice_number"].initial = generate_invoice_number(organization)


class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ("description", "quantity", "rate", "discount", "tax_rate")
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "discount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tax_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class CreditNoteForm(forms.ModelForm):
    class Meta:
        model = CreditNote
        fields = ("credit_note_number", "customer", "invoice", "date", "amount", "reason", "notes")
        widgets = {
            "credit_note_number": forms.TextInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "reason": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class DebitNoteForm(forms.ModelForm):
    class Meta:
        model = DebitNote
        fields = ("debit_note_number", "customer", "invoice", "date", "amount", "reason", "notes")
        widgets = {
            "debit_note_number": forms.TextInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "reason": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

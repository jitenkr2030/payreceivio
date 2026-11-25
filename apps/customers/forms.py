"""Customer forms."""
from django import forms

from .models import Customer, CustomerContact


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            "code", "name", "legal_name", "customer_type",
            "email", "phone", "whatsapp_number",
            "gst_number", "pan_number",
            "billing_address", "shipping_address",
            "city", "state", "country", "postal_code",
            "credit_limit", "credit_period_days",
            "opening_balance", "opening_balance_date",
            "salesperson", "territory", "department",
            "payment_terms", "preferred_payment_method",
            "opt_in_email", "opt_in_sms", "opt_in_whatsapp",
            "risk_category", "is_active",
        )
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "whatsapp_number": forms.TextInput(attrs={"class": "form-control"}),
            "gst_number": forms.TextInput(attrs={"class": "form-control"}),
            "pan_number": forms.TextInput(attrs={"class": "form-control"}),
            "billing_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "shipping_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "credit_limit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "credit_period_days": forms.NumberInput(attrs={"class": "form-control"}),
            "opening_balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "opening_balance_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "salesperson": forms.Select(attrs={"class": "form-select"}),
            "territory": forms.Select(attrs={"class": "form-select"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "payment_terms": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_payment_method": forms.Select(attrs={"class": "form-select"},
                choices=[("", "—"), ("upi", "UPI"), ("neft", "NEFT"), ("rtgs", "RTGS"),
                         ("cheque", "Cheque"), ("cash", "Cash")]),
            "risk_category": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "opt_in_email": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "opt_in_sms": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "opt_in_whatsapp": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "customer_type": forms.Select(attrs={"class": "form-select"}),
        }


class CustomerContactForm(forms.ModelForm):
    class Meta:
        model = CustomerContact
        fields = ("name", "designation", "email", "phone", "is_primary", "is_accounts_contact")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_accounts_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CustomerImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={"class": "form-control"}))

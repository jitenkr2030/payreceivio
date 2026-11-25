"""Forms for authentication and user management."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django_otp.forms import OTPAuthenticationForm

from .models import User, RoleAssignment


class LoginForm(AuthenticationForm):
    """Email-based login form."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )


class SignupForm(UserCreationForm):
    """Self-signup form for new organizations."""

    full_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    organization_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Your business name",
    )

    class Meta:
        model = User
        fields = ("full_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-control"


class RoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = RoleAssignment
        fields = ("user", "role", "company", "branch")
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "company": forms.Select(attrs={"class": "form-select"}),
            "branch": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            from apps.organizations.models import Company, Branch
            self.fields["company"].queryset = Company.objects.filter(organization=organization)
            self.fields["branch"].queryset = Branch.objects.filter(company__organization=organization)
            self.fields["role"].queryset = organization.roles.all() if hasattr(organization, "roles") else Role.objects.none()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "phone", "timezone", "date_format",
                  "notification_email", "notification_sms", "notification_whatsapp")
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "timezone": forms.Select(attrs={"class": "form-select"}),
            "date_format": forms.Select(attrs={"class": "form-select"}),
        }

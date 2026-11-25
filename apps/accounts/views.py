"""Authentication views: login, logout, signup, profile, MFA setup."""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, TemplateView
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.organizations.models import Organization
from apps.organizations.services import create_organization_with_owner

from .forms import LoginForm, SignupForm, UserProfileForm
from .models import User, UserActivity


def login_view(request):
    """Email-based login. On success, set tenant context in session."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        # Set tenant session
        org = user.get_primary_organization()
        if org:
            request.session["payreceivio_tenant"] = org.pk
        # Track activity
        UserActivity.objects.create(
            user=user,
            activity_type="login",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        messages.success(request, f"Welcome back, {user.display_name}!")
        next_url = request.GET.get("next") or "dashboard:home"
        return redirect(next_url)

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        UserActivity.objects.create(
            user=request.user,
            activity_type="logout",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


class SignupView(CreateView):
    """Self-signup: creates user + organization + org_owner role."""

    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        org = create_organization_with_owner(
            organization_name=form.cleaned_data["organization_name"],
            owner=user,
        )
        # Auto-login
        login(self.request, user)
        self.request.session["payreceivio_tenant"] = org.pk
        messages.success(self.request, f"Welcome to PayReceivio, {user.display_name}!")
        return redirect("dashboard:home")


class ProfileView(LoginRequiredMixin, UpdateView):
    """Edit personal profile."""
    model = User
    form_class = UserProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class MFASetupView(LoginRequiredMixin, TemplateView):
    """TOTP MFA setup using django-otp."""

    template_name = "accounts/mfa_setup.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if not device:
            device = TOTPDevice.objects.create(user=user, name="default", confirmed=False)
        ctx["device"] = device
        ctx["qr_url"] = device.config_url
        return ctx

    def post(self, request, *args, **kwargs):
        token = request.POST.get("token", "").strip()
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if device and device.verify_token(token):
            device.confirmed = True
            device.save()
            request.user.mfa_enabled = True
            request.user.save()
            messages.success(request, "MFA enabled successfully.")
        else:
            messages.error(request, "Invalid token. Please try again.")
        return redirect("accounts:profile")


@login_required
def switch_organization(request, org_id):
    """Switch the active organization for the session."""
    from apps.organizations.models import Organization
    try:
        org = request.user.organizations.filter(pk=org_id).first()
        if not org:
            messages.error(request, "You don't have access to that organization.")
            return redirect("dashboard:home")
    except (ValueError, Organization.DoesNotExist):
        messages.error(request, "Invalid organization.")
        return redirect("dashboard:home")

    request.session["payreceivio_tenant"] = org.pk
    # Reset company/branch
    request.session.pop("payreceivio_tenant_company", None)
    request.session.pop("payreceivio_tenant_branch", None)
    messages.success(request, f"Switched to {org.name}.")
    return redirect("dashboard:home")

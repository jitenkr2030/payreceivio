"""Disputes views."""
from django.urls import path
from django.views.generic import ListView, CreateView, DetailView
from django import forms
from django.contrib import messages
from apps.tenants.mixins import TenantMixin
from .models import Dispute


class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ("dispute_number", "customer", "invoice", "dispute_type", "amount_in_dispute", "description")
        widgets = {
            "dispute_number": forms.TextInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "dispute_type": forms.Select(attrs={"class": "form-select"}),
            "amount_in_dispute": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class DisputeListView(TenantMixin, ListView):
    model = Dispute
    template_name = "disputes/dispute_list.html"
    context_object_name = "disputes"


class DisputeCreateView(TenantMixin, CreateView):
    model = Dispute
    form_class = DisputeForm
    template_name = "disputes/dispute_form.html"

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.raised_by = self.request.user
        messages.success(self.request, "Dispute raised.")
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy("disputes:list")


class DisputeDetailView(TenantMixin, DetailView):
    model = Dispute
    template_name = "disputes/dispute_detail.html"


app_name = "disputes"
urlpatterns = [
    path("", DisputeListView.as_view(), name="list"),
    path("new/", DisputeCreateView.as_view(), name="create"),
    path("<int:pk>/", DisputeDetailView.as_view(), name="detail"),
]

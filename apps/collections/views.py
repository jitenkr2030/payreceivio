"""Collections forms and views."""
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from apps.tenants.mixins import TenantMixin

from .models import CollectionTask, FollowUp, PromiseToPay, CollectionVisit, CollectionNote


class CollectionTaskForm(forms.ModelForm):
    class Meta:
        model = CollectionTask
        fields = ("title", "description", "customer", "invoice", "assigned_to",
                  "task_type", "priority", "due_date")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "task_type": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ("customer", "invoice", "channel", "outcome", "contact_person",
                  "notes", "next_action_date", "next_action")
        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "channel": forms.Select(attrs={"class": "form-select"}),
            "outcome": forms.Select(attrs={"class": "form-select"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "next_action_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "next_action": forms.TextInput(attrs={"class": "form-control"}),
        }


class PromiseToPayForm(forms.ModelForm):
    class Meta:
        model = PromiseToPay
        fields = ("customer", "invoice", "amount", "promised_date", "source", "notes")
        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "promised_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "source": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class CollectionTaskListView(TenantMixin, ListView):
    model = CollectionTask
    template_name = "collections/task_list.html"
    context_object_name = "tasks"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class CollectionTaskCreateView(TenantMixin, CreateView):
    model = CollectionTask
    form_class = CollectionTaskForm
    template_name = "collections/task_form.html"
    success_url = reverse_lazy("collections:task_list")

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        messages.success(self.request, "Task created.")
        return super().form_valid(form)


class FollowUpListView(TenantMixin, ListView):
    model = FollowUp
    template_name = "collections/followup_list.html"
    context_object_name = "followups"
    paginate_by = 25


class FollowUpCreateView(TenantMixin, CreateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = "collections/followup_form.html"
    success_url = reverse_lazy("collections:followup_list")

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.followed_up_by = self.request.user
        messages.success(self.request, "Follow-up recorded.")
        return super().form_valid(form)


class PromiseListView(TenantMixin, ListView):
    model = PromiseToPay
    template_name = "collections/promise_list.html"
    context_object_name = "promises"
    paginate_by = 25


class PromiseCreateView(TenantMixin, CreateView):
    model = PromiseToPay
    form_class = PromiseToPayForm
    template_name = "collections/promise_form.html"
    success_url = reverse_lazy("collections:promise_list")

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.recorded_by = self.request.user
        messages.success(self.request, "Promise to pay recorded.")
        return super().form_valid(form)


class VisitListView(TenantMixin, ListView):
    model = CollectionVisit
    template_name = "collections/visit_list.html"
    context_object_name = "visits"
    paginate_by = 25

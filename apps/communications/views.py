"""Communications views."""
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, View

from apps.tenants.mixins import TenantMixin

from .models import MessageTemplate, Message, Campaign
from .services import send_message, queue_message


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ("name", "category", "channel", "subject", "body", "is_active", "is_default")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "channel": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MessageTemplateListView(TenantMixin, ListView):
    model = MessageTemplate
    template_name = "communications/template_list.html"
    context_object_name = "templates"


class MessageTemplateCreateView(TenantMixin, CreateView):
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = "communications/template_form.html"
    success_url = reverse_lazy("communications:template_list")

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        messages.success(self.request, "Template created.")
        return super().form_valid(form)


class MessageListView(TenantMixin, ListView):
    model = Message
    template_name = "communications/message_list.html"
    context_object_name = "messages"
    paginate_by = 50


class MessageDetailView(TenantMixin, DetailView):
    model = Message
    template_name = "communications/message_detail.html"
    context_object_name = "message"


class SendMessageView(TenantMixin, View):
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        message = get_object_or_404(Message, pk=pk, organization=request.active_organization)
        ok = send_message(message)
        if ok:
            messages.success(request, "Message sent.")
        else:
            messages.error(request, f"Failed to send: {message.error_message}")
        return redirect("communications:message_detail", pk=pk)


class CampaignListView(TenantMixin, ListView):
    model = Campaign
    template_name = "communications/campaign_list.html"
    context_object_name = "campaigns"


class ComposeMessageView(TenantMixin, View):
    """Compose a manual message to a customer."""
    def get(self, request, *args, **kwargs):
        from apps.customers.models import Customer
        customers = Customer.objects.filter(organization=request.active_organization, is_active=True)
        templates = MessageTemplate.objects.filter(organization=request.active_organization, is_active=True)
        return render_compose(request, customers, templates)

    def post(self, request, *args, **kwargs):
        from apps.customers.models import Customer
        customer_id = request.POST.get("customer")
        template_id = request.POST.get("template")
        channel = request.POST.get("channel", "email")
        subject = request.POST.get("subject", "")
        body = request.POST.get("body", "")
        customer = Customer.objects.get(pk=customer_id, organization=request.active_organization)
        template = MessageTemplate.objects.filter(pk=template_id).first() if template_id else None
        to = customer.email if channel == "email" else (customer.whatsapp_number or customer.phone)
        message = queue_message(
            organization=request.active_organization,
            customer=customer, template=template, channel=channel,
            to_address=to, subject=subject, body=body,
            sent_by=request.user,
        )
        messages.success(request, "Message queued.")
        return redirect("communications:message_list")


def render_compose(request, customers, templates):
    from django.shortcuts import render
    return render(request, "communications/compose.html",
                  {"customers": customers, "templates": templates})

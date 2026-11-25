"""Documents views."""
from django.urls import path
from django.views.generic import ListView, CreateView, DetailView
from django import forms
from apps.tenants.mixins import TenantMixin
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("name", "doc_type", "file", "customer", "invoice", "tags")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "doc_type": forms.Select(attrs={"class": "form-select"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.TextInput(attrs={"class": "form-control"}),
        }


class DocumentListView(TenantMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"


class DocumentCreateView(TenantMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy("documents:list")


class DocumentDetailView(TenantMixin, DetailView):
    model = Document
    template_name = "documents/document_detail.html"


app_name = "documents"
urlpatterns = [
    path("", DocumentListView.as_view(), name="list"),
    path("new/", DocumentCreateView.as_view(), name="create"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="detail"),
]

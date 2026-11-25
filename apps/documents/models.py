"""Documents models."""
from django.conf import settings
from django.db import models
from apps.common.models import TenantOwnedModel


class Document(TenantOwnedModel):
    DOC_TYPES = [
        ("invoice", "Invoice"),
        ("credit_note", "Credit Note"),
        ("debit_note", "Debit Note"),
        ("receipt", "Payment Receipt"),
        ("bank_proof", "Bank Payment Proof"),
        ("purchase_order", "Customer PO"),
        ("delivery_note", "Delivery Document"),
        ("statement", "Customer Statement"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=300)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, db_index=True)
    file = models.FileField(upload_to="documents/")
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    invoice = models.ForeignKey("receivables.Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    payment = models.ForeignKey("payments.Payment", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    tags = models.CharField(max_length=300, blank=True)
    is_shared = models.BooleanField(default=False)
    shared_at = models.DateTimeField(null=True, blank=True)
    shared_via = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to="documents/versions/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentAccessLog(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="access_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

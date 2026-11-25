"""Documents admin."""
from django.contrib import admin
from .models import Document, DocumentVersion, DocumentAccessLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "doc_type", "customer", "is_shared", "created_at")
    list_filter = ("doc_type", "is_shared")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "uploaded_by", "created_at")


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ("document", "user", "action", "created_at")

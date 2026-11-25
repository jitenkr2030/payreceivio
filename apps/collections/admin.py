"""Collections admin and API."""
from django.contrib import admin

from .models import CollectionTask, FollowUp, PromiseToPay, CollectionVisit, CollectionNote


@admin.register(CollectionTask)
class CollectionTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "assigned_to", "priority", "status", "due_date", "organization")
    list_filter = ("status", "priority", "organization")
    search_fields = ("title", "customer__name", "assigned_to__email")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("customer", "channel", "outcome", "followup_at", "followed_up_by")
    list_filter = ("channel", "outcome")


@admin.register(PromiseToPay)
class PromiseToPayAdmin(admin.ModelAdmin):
    list_display = ("customer", "amount", "promised_date", "status", "recorded_by")
    list_filter = ("status",)


@admin.register(CollectionVisit)
class CollectionVisitAdmin(admin.ModelAdmin):
    list_display = ("customer", "salesperson", "planned_at", "checked_in_at", "status")
    list_filter = ("status",)


@admin.register(CollectionNote)
class CollectionNoteAdmin(admin.ModelAdmin):
    list_display = ("customer", "note", "is_pinned", "created_at")

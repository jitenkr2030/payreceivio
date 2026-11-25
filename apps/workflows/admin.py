"""Workflows admin."""
from django.contrib import admin
from .models import Workflow, WorkflowStep, WorkflowExecution


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "trigger_event", "is_active", "priority", "total_executions")
    list_filter = ("is_active", "trigger_event")


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ("workflow", "order", "action_type")


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ("workflow", "trigger_event", "entity_type", "entity_id", "status", "started_at")
    list_filter = ("status", "trigger_event")

"""Workflow executor."""
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from .models import Workflow, WorkflowExecution, WorkflowStep


@transaction.atomic
def trigger_workflow(event_name, entity, user=None, request=None):
    """Trigger all active workflows matching this event."""
    workflows = Workflow.objects.filter(
        organization=entity.organization,
        trigger_event=event_name,
        is_active=True,
    ).order_by("priority")
    for wf in workflows:
        execute_workflow(wf, entity, user)


def execute_workflow(workflow, entity, user=None):
    """Execute a workflow against an entity (invoice/payment/customer)."""
    execution = WorkflowExecution.objects.create(
        workflow=workflow,
        triggered_by=user,
        trigger_event=workflow.trigger_event,
        entity_type=entity.__class__.__name__.lower(),
        entity_id=str(entity.pk),
    )
    steps = workflow.steps.order_by("order")
    log = []
    try:
        for step in steps:
            log.append({"step": step.order, "action": step.action_type, "status": "started"})
            _execute_step(step, entity, user, log)
            log.append({"step": step.order, "action": step.action_type, "status": "completed"})
            execution.current_step = step.order
            execution.save()
        execution.status = "completed"
        workflow.successful_executions += 1
    except Exception as e:
        execution.status = "failed"
        execution.error_message = str(e)
        workflow.failed_executions += 1
        log.append({"error": str(e)})
    execution.log = log
    execution.completed_at = timezone.now()
    execution.save()
    workflow.total_executions += 1
    workflow.last_run_at = timezone.now()
    workflow.save()
    return execution


def _execute_step(step, entity, user, log):
    """Execute a single workflow step."""
    if step.action_type == "send_message":
        from apps.communications.services import queue_message
        from apps.communications.models import MessageTemplate
        template_id = step.config.get("template_id")
        channel = step.config.get("channel", "email")
        template = MessageTemplate.objects.filter(id=template_id).first()
        if template and hasattr(entity, "customer"):
            queue_message(
                organization=entity.organization,
                customer=entity.customer,
                invoice=entity if entity.__class__.__name__ == "Invoice" else None,
                payment=entity if entity.__class__.__name__ == "Payment" else None,
                template=template,
                channel=channel,
                to_address=getattr(entity.customer, "email", "") if channel == "email"
                            else (getattr(entity.customer, "whatsapp_number", "") or getattr(entity.customer, "phone", "")),
                sent_by=user,
            )
    elif step.action_type == "create_task":
        from apps.collections.models import CollectionTask
        if hasattr(entity, "customer"):
            CollectionTask.objects.create(
                organization=entity.organization,
                customer=entity.customer,
                invoice=entity if entity.__class__.__name__ == "Invoice" else None,
                title=step.config.get("title", "Follow-up task"),
                description=step.config.get("description", ""),
                task_type=step.config.get("task_type", "call"),
                priority=step.config.get("priority", "medium"),
                due_date=timezone.now().date() + timedelta(days=step.config.get("due_in_days", 1)),
                assigned_to=user,
                created_by=user,
            )
    elif step.action_type == "wait":
        # In a real system, this would pause the workflow. For now, just log.
        pass
    elif step.action_type == "escalate":
        if hasattr(entity, "customer"):
            from apps.collections.models import CollectionTask
            CollectionTask.objects.create(
                organization=entity.organization,
                customer=entity.customer,
                title=f"Escalation: {entity.customer.name}",
                description=f"Escalated via workflow. Reason: {step.config.get('reason', '')}",
                task_type="escalation",
                priority="urgent",
                due_date=timezone.now().date(),
                assigned_to=user,
                created_by=user,
                escalation_level=step.config.get("level", 1),
            )

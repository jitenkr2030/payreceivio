"""AI Assistant views."""
from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path
from django.views.generic import TemplateView

from apps.tenants.mixins import TenantMixin

from .models import Conversation as AIConversation, Message as AIMessage
from .services import answer_question, draft_reminder_message


class AIChatView(TenantMixin, TemplateView):
    template_name = "ai/chat.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Get or create a conversation for the user
        conv, _ = AIConversation.objects.get_or_create(
            user=self.request.user,
            organization=self.request.active_organization,
            is_active=True,
        )
        ctx["conversation"] = conv
        ctx["messages"] = conv.messages.all()[:50]
        ctx["suggested_questions"] = [
            "How much money is overdue today?",
            "Which 20 customers have the highest outstanding balances?",
            "Which customers have not paid within 60 days?",
            "What amount should we expect to collect this week?",
            "Which salesperson has the lowest collection performance?",
            "Show customers whose payment delays are increasing.",
            "Which bank transactions have not been matched?",
            "What is our Days Sales Outstanding (DSO)?",
        ]
        return ctx

    def post(self, request, *args, **kwargs):
        question = request.POST.get("question", "").strip()
        if not question:
            return redirect("ai:chat")
        conv, _ = AIConversation.objects.get_or_create(
            user=request.user, organization=request.active_organization, is_active=True,
        )
        AIMessage.objects.create(conversation=conv, role="user", content=question)
        result = answer_question(question, request.active_organization, request.user)
        AIMessage.objects.create(
            conversation=conv, role="assistant",
            content=result["answer"], intent=result["intent"],
            sources=result["sources"],
        )
        conv.title = question[:80]
        conv.save()
        return redirect("ai:chat")


app_name = "ai"
urlpatterns = [
    path("chat/", AIChatView.as_view(), name="chat"),
]

"""Notifications views."""
from django.http import JsonResponse
from django.urls import path
from django.views import View
from django.views.generic import ListView

from apps.tenants.mixins import TenantMixin
from .models import Notification


class NotificationListView(TenantMixin, ListView):
    model = Notification
    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 50

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class MarkReadView(View):
    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save()
        return JsonResponse({"ok": True})


class UnreadCountView(View):
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({"count": count})


app_name = "notifications"
urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("<int:pk>/read/", MarkReadView.as_view(), name="mark_read"),
    path("unread-count/", UnreadCountView.as_view(), name="unread_count"),
]

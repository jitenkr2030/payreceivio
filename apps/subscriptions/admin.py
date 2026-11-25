"""Subscriptions admin and API."""
from django.contrib import admin
from .models import Plan, Subscription, UsageRecord, BillingInvoice


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "monthly_price", "annual_price", "is_active")
    list_filter = ("is_active", "is_trial")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("organization", "plan", "status", "billing_cycle", "started_at", "current_period_end")
    list_filter = ("status", "billing_cycle", "plan")


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ("organization", "period_start", "period_end", "invoice_count", "message_count", "user_count")


@admin.register(BillingInvoice)
class BillingInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "organization", "invoice_date", "total_amount", "status")
    list_filter = ("status",)


from rest_framework import serializers, viewsets


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filterset_fields = ["organization", "status"]

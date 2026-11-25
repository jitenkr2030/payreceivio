"""Communications admin and API."""
from django.contrib import admin

from .models import MessageTemplate, Message, Campaign, Conversation, ConversationMessage


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "channel", "is_active", "is_default")
    list_filter = ("channel", "category", "is_active")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("customer", "channel", "subject", "status", "sent_at")
    list_filter = ("status", "channel")


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "template", "channel", "status", "total_recipients", "sent_count")
    list_filter = ("status", "channel")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("customer", "channel", "status", "last_message_at")


from rest_framework import serializers, viewsets


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filterset_fields = ["customer", "channel", "status", "template"]
    search_fields = ["subject", "body", "to_address"]


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    filterset_fields = ["status", "channel"]

"""Communications DRF API views."""
from rest_framework import serializers, viewsets

from .models import Message, Campaign


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

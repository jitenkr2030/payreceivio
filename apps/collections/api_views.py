"""Collections DRF API."""
from rest_framework import serializers, viewsets

from .models import CollectionTask, FollowUp, PromiseToPay


class CollectionTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionTask
        fields = "__all__"


class CollectionTaskViewSet(viewsets.ModelViewSet):
    queryset = CollectionTask.objects.all()
    serializer_class = CollectionTaskSerializer
    filterset_fields = ["customer", "assigned_to", "status", "priority", "task_type"]
    search_fields = ["title", "customer__name"]

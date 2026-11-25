"""DRF API views for accounts."""
from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User, Role, RoleAssignment


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=True)
    organizations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "is_active", "mfa_enabled",
                  "organizations", "date_joined")
        read_only_fields = ("id", "date_joined", "organizations")

    def get_organizations(self, obj):
        return [{"id": o.id, "name": o.name} for o in obj.organizations]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["is_active", "mfa_enabled"]
    search_fields = ["email", "full_name", "phone"]
    ordering_fields = ["date_joined", "email"]

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

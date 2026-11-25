"""DRF API views for organizations."""
from rest_framework import serializers, viewsets

from .models import Organization, Company, Branch


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "legal_name", "email", "phone", "gst_number",
                  "currency", "is_active", "subscription_plan", "trial_ends_at")


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "organization", "name", "legal_name", "email", "phone",
                  "gst_number", "currency", "is_active")


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "company", "name", "code", "email", "phone",
                  "is_active", "is_head_office")


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filterset_fields = ["organization", "is_active"]


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    filterset_fields = ["company", "is_active"]

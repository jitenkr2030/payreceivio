"""Analytics DRF API views."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services import compute_kpis


class DashboardMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = getattr(request, "active_organization", None)
        if not org:
            return Response({"error": "no_active_organization"}, status=400)
        return Response(compute_kpis(org))

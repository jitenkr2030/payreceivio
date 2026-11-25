"""Dashboard URLs (alias to analytics owner dashboard)."""
from django.urls import path
from django.views.generic import RedirectView

from apps.analytics.views import DashboardHomeView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
]

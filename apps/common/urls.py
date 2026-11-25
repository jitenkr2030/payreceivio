"""Common URL routes - dashboard home."""
from django.urls import path
from django.views.generic import TemplateView

app_name = "common"


class HomeView(TemplateView):
    template_name = "base/landing.html"


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]

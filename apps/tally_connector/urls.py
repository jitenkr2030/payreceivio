"""Tally connector URLs."""
from django.urls import path
from django.views.generic import TemplateView

app_name = "tally"


class TallyDocsView(TemplateView):
    template_name = "tally/docs.html"


urlpatterns = [
    path("docs/", TallyDocsView.as_view(), name="docs"),
]

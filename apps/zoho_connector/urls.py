"""Zoho connector URLs."""
from django.http import HttpResponse
from django.urls import path
from django.views.generic import TemplateView

app_name = "zoho"


class ZohoDocsView(TemplateView):
    template_name = "zoho/docs.html"


def oauth_callback(request):
    """OAuth 2.0 callback handler - exchanges code for tokens."""
    code = request.GET.get("code")
    state = request.GET.get("state")
    # In production: exchange code for tokens and store in AccountingConnection
    return HttpResponse(f"OAuth callback received. Code: {code[:10]}...")


urlpatterns = [
    path("docs/", ZohoDocsView.as_view(), name="docs"),
    path("oauth/callback/", oauth_callback, name="oauth_callback"),
]

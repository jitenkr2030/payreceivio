"""URLs for the accounting_connectors app - documentation pages."""
from django.urls import path
from django.views.generic import TemplateView

app_name = "accounting_connectors"


class ConnectorDocsView(TemplateView):
    """Generic docs view for a single connector."""
    template_name = "connectors/docs.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        connector_name = self.kwargs.get("connector_name")
        ctx["connector_name"] = connector_name
        ctx["connector_docs"] = CONNECTOR_DOCS.get(connector_name, {})
        return ctx


class ConnectorListView(TemplateView):
    template_name = "connectors/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["connectors"] = [
            {"name": k, **v} for k, v in CONNECTOR_DOCS.items()
        ]
        return ctx


CONNECTOR_DOCS = {
    "busy": {"label": "BUSY", "vendor": "BUSY Infotech", "auth": "API Token",
             "url": "http://localhost:5400/api/v1/",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "marg": {"label": "Marg ERP", "vendor": "Marg Compusolutions", "auth": "API Key",
             "url": "http://localhost:8999/api/",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "quickbooks": {"label": "QuickBooks Online", "vendor": "Intuit", "auth": "OAuth 2.0",
                   "url": "https://quickbooks.api.intuit.com/v3/company/",
                   "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "xero": {"label": "Xero", "vendor": "Xero", "auth": "OAuth 2.0",
             "url": "https://api.xero.com/api.xro/2.0/",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "sage": {"label": "Sage Business Cloud", "vendor": "Sage", "auth": "OAuth 2.0",
             "url": "https://api.accounting.sage.com/v3.1/",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "dynamics365": {"label": "Microsoft Dynamics 365 BC", "vendor": "Microsoft", "auth": "OAuth 2.0 (Azure AD)",
                    "url": "https://api.businesscentral.dynamics.com/v2.0/",
                    "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "netsuite": {"label": "Oracle NetSuite", "vendor": "Oracle", "auth": "OAuth 2.0",
                 "url": "https://{account}.suitetalk.api.netsuite.com/services/rest/record/v1/",
                 "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "sap_b1": {"label": "SAP Business One", "vendor": "SAP", "auth": "Service Layer Session",
               "url": "http://localhost:50000/b1s/v1/",
               "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "odoo": {"label": "Odoo", "vendor": "Odoo S.A.", "auth": "Database + API Key (XML-RPC)",
             "url": "{host}/xmlrpc/2/",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "myob": {"label": "MYOB AccountRight", "vendor": "MYOB", "auth": "OAuth 2.0",
             "url": "https://api.myob.com/accountright/",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "freshbooks": {"label": "FreshBooks", "vendor": "FreshBooks", "auth": "OAuth 2.0",
                   "url": "https://api.freshbooks.com/",
                   "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "wave": {"label": "Wave Financial", "vendor": "Wave", "auth": "OAuth 2.0 + GraphQL",
             "url": "https://gql.waveapps.com/graphql/public",
             "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "gofrugal": {"label": "GoFrugal", "vendor": "GoFrugal Technologies", "auth": "API Key",
                 "url": "http://localhost:8505/api/",
                 "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "focus": {"label": "Focus Softnet", "vendor": "Focus Softnet", "auth": "JWT",
              "url": "http://localhost:8080/iconnect/api/v1/",
              "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "exact": {"label": "Exact Online", "vendor": "Exact", "auth": "OAuth 2.0",
              "url": "https://start.exactonline.nl/api/v1/",
              "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "autocount": {"label": "AutoCount", "vendor": "AutoCount Sdn Bhd", "auth": "API Key",
                  "url": "http://localhost:8081/autocount/api/",
                  "entities": ["customer", "invoice", "credit_note", "receipt"]},
    "money_forward": {"label": "Money Forward Cloud", "vendor": "Money Forward", "auth": "OAuth 2.0",
                      "url": "https://api.moneyforward.com/api/v1/",
                      "entities": ["customer", "invoice", "credit_note", "receipt"]},
}


urlpatterns = [
    path("", ConnectorListView.as_view(), name="list"),
    path("<str:connector_name>/", ConnectorDocsView.as_view(), name="docs"),
]

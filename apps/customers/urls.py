from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="list"),
    path("new/", views.CustomerCreateView.as_view(), name="create"),
    path("import/", views.CustomerImportView.as_view(), name="import"),
    path("<int:pk>/", views.CustomerDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="update"),
    path("<int:pk>/statement/", views.CustomerStatementView.as_view(), name="statement"),
    path("<int:pk>/ledger/", views.CustomerLedgerView.as_view(), name="ledger"),
]

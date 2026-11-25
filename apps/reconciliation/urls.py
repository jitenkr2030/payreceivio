from django.urls import path

from . import views

app_name = "reconciliation"

urlpatterns = [
    path("bank-accounts/", views.BankAccountListView.as_view(), name="bank_list"),
    path("statements/", views.BankStatementListView.as_view(), name="statement_list"),
    path("statements/new/", views.ImportStatementView.as_view(), name="statement_new"),
    path("statements/<int:pk>/upload/", views.UploadStatementView.as_view(), name="upload"),
    path("unmatched/", views.UnmatchedTransactionListView.as_view(), name="unmatched"),
    path("transactions/<int:pk>/match/", views.MatchSuggestionView.as_view(), name="match"),
    path("transactions/<int:pk>/ignore/", views.IgnoreTransactionView.as_view(), name="ignore"),
    path("matches/", views.ReconciliationListView.as_view(), name="matches"),
]

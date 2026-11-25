from django.urls import path

from . import views

app_name = "receivables"

urlpatterns = [
    path("invoices/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoices/new/", views.InvoiceCreateView.as_view(), name="invoice_create"),
    path("invoices/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("invoices/<int:pk>/edit/", views.InvoiceUpdateView.as_view(), name="invoice_update"),
    path("invoices/overdue/", views.OverdueInvoiceListView.as_view(), name="invoice_overdue"),
    path("invoices/due-today/", views.DueTodayListView.as_view(), name="invoice_due_today"),
    path("invoices/upcoming/", views.UpcomingListView.as_view(), name="invoice_upcoming"),
    path("credit-notes/", views.CreditNoteListView.as_view(), name="creditnote_list"),
    path("credit-notes/new/", views.CreditNoteCreateView.as_view(), name="creditnote_create"),
    path("debit-notes/", views.DebitNoteListView.as_view(), name="debitnote_list"),
    path("debit-notes/new/", views.DebitNoteCreateView.as_view(), name="debitnote_create"),
]

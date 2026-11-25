from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.PaymentListView.as_view(), name="list"),
    path("new/", views.PaymentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PaymentDetailView.as_view(), name="detail"),
    path("<int:pk>/allocate/", views.PaymentAllocateView.as_view(), name="allocate"),
    path("links/", views.PaymentLinkListView.as_view(), name="link_list"),
    path("links/new/", views.PaymentLinkCreateView.as_view(), name="link_create"),
    path("refunds/", views.RefundListView.as_view(), name="refund_list"),
]

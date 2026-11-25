from django.urls import path

from . import views

app_name = "communications"

urlpatterns = [
    path("templates/", views.MessageTemplateListView.as_view(), name="template_list"),
    path("templates/new/", views.MessageTemplateCreateView.as_view(), name="template_create"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/", views.MessageDetailView.as_view(), name="message_detail"),
    path("messages/<int:pk>/send/", views.SendMessageView.as_view(), name="message_send"),
    path("compose/", views.ComposeMessageView.as_view(), name="compose"),
    path("campaigns/", views.CampaignListView.as_view(), name="campaign_list"),
]

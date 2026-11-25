from django.urls import path

from . import views

app_name = "collections"

urlpatterns = [
    path("tasks/", views.CollectionTaskListView.as_view(), name="task_list"),
    path("tasks/new/", views.CollectionTaskCreateView.as_view(), name="task_create"),
    path("followups/", views.FollowUpListView.as_view(), name="followup_list"),
    path("followups/new/", views.FollowUpCreateView.as_view(), name="followup_create"),
    path("promises/", views.PromiseListView.as_view(), name="promise_list"),
    path("promises/new/", views.PromiseCreateView.as_view(), name="promise_create"),
    path("visits/", views.VisitListView.as_view(), name="visit_list"),
]

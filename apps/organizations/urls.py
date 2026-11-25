from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.OrganizationListView.as_view(), name="list"),
    path("companies/", views.CompanyListView.as_view(), name="company_list"),
    path("branches/", views.BranchListView.as_view(), name="branch_list"),
    path("departments/", views.DepartmentListView.as_view(), name="department_list"),
    path("territories/", views.TerritoryListView.as_view(), name="territory_list"),
    path("roles/", views.RoleAssignmentListView.as_view(), name="role_list"),
    path("roles/new/", views.RoleAssignmentCreateView.as_view(), name="role_create"),
]

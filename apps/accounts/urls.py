from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("mfa/setup/", views.MFASetupView.as_view(), name="mfa_setup"),
    path("switch-org/<int:org_id>/", views.switch_organization, name="switch_org"),
]

from django.urls import path

from .views import LoginView, LogoutView, MePasswordView, MeView, RefreshView, UserDetailView, UserListCreateView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth_login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("me", MeView.as_view(), name="me"),
    path("me/password", MePasswordView.as_view(), name="me_password"),
    path("users", UserListCreateView.as_view(), name="user_list_create"),
    path("users/<int:user_id>", UserDetailView.as_view(), name="user_detail"),
]

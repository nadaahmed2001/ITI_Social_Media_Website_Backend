from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterStudentView, LoginView, LogoutView, UserProfileView

urlpatterns = [
    path("register/", RegisterStudentView.as_view(), name="register_student"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),

    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]



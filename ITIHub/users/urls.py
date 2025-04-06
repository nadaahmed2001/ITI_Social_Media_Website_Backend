from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterStudentView, LoginView, LogoutView, UserProfileView, AllProfilesAPI, UserProfileAPI, SkillAPI, PasswordResetRequestView,  PasswordResetConfirmView ,UserAccountAPI

urlpatterns = [
    path("register/", RegisterStudentView.as_view(), name="register_student"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),

    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    path('profiles/', AllProfilesAPI.as_view(), name="all_profiles"),
    path('profiles/<str:id>', UserProfileAPI.as_view(), name='user_profile'),
    
    path('account/', UserAccountAPI.as_view(), name='user_account_api'), # For getting, and updating the user account
    # Skill api
    path('skills/', SkillAPI.as_view(), name='get_all_skills_api'),  # For getting all skills
    path('skills/<uuid:pk>/', SkillAPI.as_view(), name='skill_api'),  # For getting, updating, and deleting a specific skill


    #reset password urls
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]



from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
                    RegisterStudentView, 
                    LoginView, 
                    LogoutView, 
                    UserProfileView, 
                    AllProfilesAPI, 
                    UserProfileAPI, 
                    SkillAPI, 
                    UserAccountAPI,
                    ChangePasswordView,
                    ChangeEmailView,
                    ConfirmEmailChangeView,
                    )

urlpatterns = [
    path("register/", RegisterStudentView.as_view(), name="register_student"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Skill api
    path('skills/', SkillAPI.as_view(), name='get_all_skills_api'),      # For getting all skills
    path('skills/<uuid:pk>/', SkillAPI.as_view(), name='skill_api'),     # For getting, updating, and deleting a specific skill
    
    path("profile/", UserProfileView.as_view(), name="user_profile"),   # For getting signed-in user profile
    path('profiles/', AllProfilesAPI.as_view(), name="all_profiles"),            # For getting all profiles
    path('profiles/<str:id>/', UserProfileAPI.as_view(), name='user_profile'),   # For getting a profile by user id
    
    # User Account
    path('account/', UserAccountAPI.as_view(), name='user_account_api'), # For getting, and updating the user account
    
    # User Profile - Change password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # User Profile - Change E-mail
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),
    path('confirm-email-change/<uuid:token>/', ConfirmEmailChangeView.as_view(), name='confirm-email-change'),

]



from django.urls import path
from django.contrib.auth import views as auth_views
from .views import  supervisor_login_view, supervisor_logout, student_login, student_logout, student_dashboard, student_register

urlpatterns = [
    path("supervisor/login/", supervisor_login_view, name="supervisor_login"),
    path("supervisor/logout/", supervisor_logout, name="supervisor_logout"),
    path("student/login/", student_login, name="student_login"),
    path("student/register/", student_register, name="student_register"),
    path("student/logout/", student_logout, name="student_logout"),
    path("student/dashboard/", student_dashboard, name="student_dashboard"),
]


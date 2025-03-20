from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('program_details/<int:program_id>/', views.program_details, name='program_details')

]
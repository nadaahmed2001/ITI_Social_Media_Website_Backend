from django.urls import path
from . import views
from .views import create_batch, dashboard, program_details, track_batches


urlpatterns = [
    path('supervisor_dashboard/', views.dashboard, name='supervisor_dashboard'),
    path('program_details/<int:program_id>/', views.program_details, name='program_details'),
    path('track_batches/<int:track_id>/', views.track_batches, name='track_batches'),
    path("create-batch/", create_batch, name="create_batch"),
    

]
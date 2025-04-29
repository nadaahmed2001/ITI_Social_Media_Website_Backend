from django.urls import path
from . import views

urlpatterns = [
    path('api/websocket-config/', views.websocket_config, name='websocket-config'),
]

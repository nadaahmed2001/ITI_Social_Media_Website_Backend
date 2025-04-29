from django.urls import path
from . import views
from . import websocket_debug

urlpatterns = [
    path('websocket-config/', views.websocket_config, name='websocket_config'),
    path('websocket-diagnostics/', websocket_debug.websocket_diagnostics, name='websocket_diagnostics'),
]

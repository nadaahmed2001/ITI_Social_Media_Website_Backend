from django.urls import path
from . import views
from . import websocket_debug
from . import websocket_health

urlpatterns = [
    path('websocket-config/', views.websocket_config, name='websocket_config'),
    path('websocket-diagnostics/', websocket_debug.websocket_diagnostics, name='websocket_diagnostics'),
    path('websocket-health/', websocket_health.websocket_health, name='websocket_health'),
]

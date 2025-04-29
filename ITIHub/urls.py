from django.contrib import admin
from django.urls import path

# Import the views
from core.websocket_connection_test import test_websocket_connection, html_websocket_tester
from core.views import websocket_config
from core.websocket_debug import websocket_diagnostics
from core.websocket_health import websocket_health
from core.websocket_token_test import test_token

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # WebSocket configuration and diagnostics endpoints
    path('api/ws/config/', websocket_config, name='websocket_config'),
    path('api/ws/health/', websocket_health, name='websocket_health'),
    path('api/ws/diagnostics/', websocket_diagnostics, name='websocket_diagnostics'),
    
    # WebSocket testing endpoints
    path('api/ws/test-connection/', test_websocket_connection, name='test_websocket_connection'),
    path('api/ws/test/', html_websocket_tester, name='html_websocket_tester'),
    path('api/ws/test-token/', test_token, name='test_token'),
]

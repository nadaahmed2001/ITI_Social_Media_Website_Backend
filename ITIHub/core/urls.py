from django.urls import path
from . import views
from . import websocket_debug
from . import websocket_health
from . import websocket_connection_test
from . import websocket_token_test

urlpatterns = [
    # Add root path handler
    path('', views.index, name='index'),
    path('websocket-config/', views.websocket_config, name='websocket_config'),
    path('websocket-diagnostics/', websocket_debug.websocket_diagnostics, name='websocket_diagnostics'),
    path('websocket-health/', websocket_health.websocket_health, name='websocket_health'),
    path('websocket-test/', websocket_connection_test.test_websocket_connection, name='websocket_test'),
    path('websocket-html-tester/', websocket_connection_test.html_websocket_tester, name='websocket_html_tester'),
    path('test-token/', websocket_token_test.test_token, name='test_token'),
    # New dedicated health-check endpoint for frontend
    path('health-check/', views.health_check, name='health_check'),
]

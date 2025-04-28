import os
import django

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')
django.setup()

# Import your WebSocket routing after Django setup
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from chat.middleware import TokenAuthMiddlewareStack  # Import the custom middleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddlewareStack(  # Use TokenAuthMiddleware instead of AuthMiddlewareStack
        URLRouter(
            chat_websocket_urlpatterns
        )
    ),
})
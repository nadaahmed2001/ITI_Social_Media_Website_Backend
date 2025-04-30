import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import logging

# Configure logging early
logger = logging.getLogger(__name__)

# Set Django settings and setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')
django.setup()

# Log the setup process
logger.info("ASGI application initializing...")

# Import after Django setup to avoid import errors
from channels.auth import AuthMiddlewareStack
from chat.middleware import TokenAuthMiddlewareStack
from chat.routing import websocket_urlpatterns

# Create the ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

# Log successful setup
logger.info("ASGI application initialized successfully")
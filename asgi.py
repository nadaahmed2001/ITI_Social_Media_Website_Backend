"""
ASGI config for ITIHub project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from ITIHub.chat.middleware import TokenAuthMiddlewareStack
from chat.routing import websocket_urlpatterns
from .asgi_timeout import with_timeout

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# Apply timeout middleware to the entire application
application = with_timeout(
    ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
)

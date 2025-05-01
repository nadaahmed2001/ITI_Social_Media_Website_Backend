from django.urls import re_path, path
from . import consumers

# Both routing styles are provided - the typed path converters are more specific
# and safer as they validate the type, but regex is more flexible
websocket_urlpatterns = [
    # Type-enforced paths (recommended for better type safety)
    path('ws/chat/group/<int:group_id>/', consumers.GroupChatConsumer.as_asgi()),
    path('ws/chat/private/<int:user_id>/', consumers.PrivateChatConsumer.as_asgi()),
    
    # Legacy regex paths (kept for backward compatibility)
    re_path(r"ws/chat/group/(?P<group_id>\w+)/$", consumers.GroupChatConsumer.as_asgi()),
    re_path(r"ws/chat/private/(?P<user_id>\w+)/$", consumers.PrivateChatConsumer.as_asgi()),
]
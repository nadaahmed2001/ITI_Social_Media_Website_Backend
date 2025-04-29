from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Group chat route - matches /ws/chat/group/1/
    re_path(r'^ws/chat/group/(?P<group_id>\w+)/$', consumers.GroupChatConsumer.as_asgi()),
    
    # Private chat route - matches /ws/chat/private/1/
    re_path(r'^ws/chat/private/(?P<user_id>\w+)/$', consumers.PrivateChatConsumer.as_asgi()),
]

# filepath: /home/nizar/Desktop/iti_social_meidia/ITI_Social_Media_Website_Backend/ITIHub/chat/routing.py
from django.urls import path
from .consumers import GroupChatConsumer, PrivateChatConsumer

websocket_urlpatterns = [
    path('ws/chat/group/<int:group_id>/', GroupChatConsumer.as_asgi()),
    path('ws/chat/private/<int:user_id>/', PrivateChatConsumer.as_asgi()),
]

# filepath: /home/nizar/Desktop/iti_social_meidia/ITI_Social_Media_Website_Backend/ITIHub/chat/routing.py
from django.urls import path
from .consumers import GroupChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<int:group_id>/', GroupChatConsumer.as_asgi()),
]
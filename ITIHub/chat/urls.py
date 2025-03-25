from django.urls import path
from .views import GroupChatListCreateView, GroupChatDetailView, GroupMessageListCreateView, ChatMessageListCreateView, UserChatListView

urlpatterns = [
    path('groups/', GroupChatListCreateView.as_view(), name='group_chat_list_create'),
    path('groups/<int:pk>/', GroupChatDetailView.as_view(), name='group_chat_detail'),
    path('groups/<int:group_id>/messages/', GroupMessageListCreateView.as_view(), name='group_message_list_create'),
    path('messages/<int:receiver_id>/', ChatMessageListCreateView.as_view(), name='chat_message_list_create'),
    path('group_messages/<int:group_chat>/', ChatMessageListCreateView.as_view(), name='group_chat_message_list_create'),
    path('user_chats/<int:user_id>/', UserChatListView.as_view(), name='user_chat_list'),
]

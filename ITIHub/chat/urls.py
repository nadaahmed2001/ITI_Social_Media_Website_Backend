from django.urls import path
from .views import (
    GroupChatListCreateView, GroupChatDetailView, GroupMessageListCreateView,
    ChatMessageListCreateView, UserChatDashboardView, PrivateChatUsersView,
    ClearGroupChatView, ClearPrivateChatView, EditMessageView, DeleteMessageView, delete_group_message, ChatBotView, ChatBotMessagesView, EditGroupMessageView
)

urlpatterns = [
    path('groups/', GroupChatListCreateView.as_view(), name='group_chat_list_create'),
    path('groups/<int:pk>/', GroupChatDetailView.as_view(), name='group_chat_detail'),
    path('groups/<int:group_id>/messages/', GroupMessageListCreateView.as_view(), name='group_message_list_create'),
    path('messages/<int:receiver_id>/', ChatMessageListCreateView.as_view(), name='chat_message_list_create'),
    path('user_chats/', UserChatDashboardView.as_view(), name='user_chat_dashboard'),
    path('private_chat_users/', PrivateChatUsersView.as_view(), name='private_chat_users'),  
    path('group-chats/<int:group_id>/clear/', ClearGroupChatView.as_view(), name='clear-group-chat'),
    path('private-chats/<int:receiver_id>/clear/', ClearPrivateChatView.as_view(), name='clear-private-chat'),
    path('messages/<int:message_id>/edit/', EditMessageView.as_view(), name='edit-message'),
    path('messages/<int:message_id>/delete/', DeleteMessageView.as_view(), name='delete-message'),
    path('groups/<int:group_id>/messages/<int:message_id>/delete/', delete_group_message, name='delete-group-message'),
    path('chatbot/', ChatBotView.as_view(), name='chatbot'),
    path('chatbot/messages/', ChatBotMessagesView.as_view(), name='chatbot-messages'),
    path('groups/<int:group_id>/messages/<int:message_id>/edit/', EditGroupMessageView.as_view(), name='edit-group-message'),
]

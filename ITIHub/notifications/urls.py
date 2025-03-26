from django.urls import path
from .views import (
    NotificationListView,
    UnreadNotificationsView,
    ChatNotificationsView,
    GroupChatNotificationsView,
    UnreadChatNotificationsView,
    MarkNotificationAsRead,
    MarkAllNotificationsAsRead,
    DeleteNotification,
    ClearAllNotifications,
    PostNotificationsView,
    MarkPostNotificationsAsRead,
    DeletePostNotifications,  
    UnreadPostNotificationsView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='all-notifications'),
     path('unread/', UnreadNotificationsView.as_view(), name='unread-notifications'),
    path('mark-all-as-read/', MarkAllNotificationsAsRead.as_view(), name='mark_all_notifications_as_read'),
    path('clear-all/', ClearAllNotifications.as_view(), name='clear-all-notifications'),

    path('<int:notification_id>/mark-as-read/', MarkNotificationAsRead.as_view(), name='mark_notification_as_read'),
    path('<int:notification_id>/', DeleteNotification.as_view(), name='delete-notification'),
    
    path('chat/', ChatNotificationsView.as_view(), name='chat-notifications'),
    path('group-chat/', GroupChatNotificationsView.as_view(), name='group-chat-notifications'),
    path('chat/unread/', UnreadChatNotificationsView.as_view(), name='unread-chat-notifications'),

    path('posts/', PostNotificationsView.as_view(), name='post-notifications'),
    path('posts/mark-all-as-read/', MarkPostNotificationsAsRead.as_view(), name='mark-post-notifications-read'),
    path('posts/delete-all/', DeletePostNotifications.as_view(), name='delete-post-notifications'),
    path('posts/unread/', UnreadPostNotificationsView.as_view(), name='unread-post-notifications'),
]

from django.urls import path
from .views import (
    AllNotificationsView,
    ChatNotificationsView,
    GroupChatNotificationsView,
    MarkNotificationAsRead,
    MarkAllNotificationsAsRead,
    DeleteNotification,
    ClearAllNotifications,
)

urlpatterns = [
    # Chat Notification
    path('', AllNotificationsView.as_view(), name='all-notifications'),
    path('chat/', ChatNotificationsView.as_view(), name='chat-notifications'),
    path('group-chat/', GroupChatNotificationsView.as_view(), name='group-chat-notifications'),
    path('<int:notification_id>/mark-as-read/', MarkNotificationAsRead.as_view(), name='mark_notification_as_read'),
    path('mark-all-as-read/', MarkAllNotificationsAsRead.as_view(), name='mark_all_notifications_as_read'),
    path('<int:notification_id>/', DeleteNotification.as_view(), name='delete-notification'),
    path('clear-all/', ClearAllNotifications.as_view(), name='clear-all-notifications'),


]

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    notification_types = [] 

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        if self.notification_types:
            queryset = queryset.filter(notification_type__in=self.notification_types)
        return queryset.order_by('-created_at')

class UnreadNotificationsView(NotificationListView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).order_by('-created_at')


class ChatNotificationsView(NotificationListView):
    notification_types = ["chat"]


class GroupChatNotificationsView(NotificationListView):
    notification_types = ["group_chat"]


class UnreadChatNotificationsView(NotificationListView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            notification_type__in=["chat", "group_chat"], 
            is_read=False
        ).order_by('-created_at')


class PostNotificationsView(NotificationListView):
    notification_types = ["new_post", "comment", "mention", "reaction"]

class UnreadPostNotificationsView(NotificationListView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            notification_type__in=["new_post", "comment", "mention"],  
            is_read=False
        ).order_by('-created_at')


class MarkNotificationAsRead(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, notification_id):
        notification = Notification.objects.filter(id=notification_id, recipient=request.user).first()
        if not notification:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)


class MarkPostNotificationsAsRead(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        updated_count = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=["new_post", "comment", "mention", "reaction"],
            is_read=False
        ).update(is_read=True)

        return Response(
            {"message": f"{updated_count} post notifications marked as read"},
            status=status.HTTP_200_OK
        )

class DeletePostNotifications(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = Notification.objects.filter(
            recipient=request.user,
            notification_type__in=["new_post", "comment", "mention", "reaction"]
        ).delete()

        return Response(
            {"message": f"{deleted_count} post notifications deleted"},
            status=status.HTTP_200_OK
        )


class MarkAllNotificationsAsRead(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        notification_type = request.query_params.get('type', '').strip()
        filters = {"recipient": request.user, "is_read": False}
        
        if notification_type:
            filters["notification_type"] = notification_type

        updated_count = Notification.objects.filter(**filters).update(is_read=True)

        return Response(
            {"message": f"{updated_count} notifications marked as read"},
            status=status.HTTP_200_OK
        )


class DeleteNotification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, notification_id):
        deleted_count, _ = Notification.objects.filter(id=notification_id, recipient=request.user).delete()
        if deleted_count == 0:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Notification deleted"}, status=status.HTTP_200_OK)


class ClearAllNotifications(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        notification_type = request.query_params.get('type', '').strip()
        filters = {"recipient": request.user}

        if notification_type:
            filters["notification_type"] = notification_type

        deleted_count, _ = Notification.objects.filter(**filters).delete()
        return Response(
            {"message": f"{deleted_count} notifications deleted"},
            status=status.HTTP_200_OK
        )

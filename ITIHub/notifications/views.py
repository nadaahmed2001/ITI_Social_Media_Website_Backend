from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

#show all notification
class AllNotificationsView(generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        notification_type = self.request.query_params.get('type', '').strip()
        if notification_type:
            queryset = queryset.filter(notification_type__iexact=notification_type)
        else:
            queryset = queryset.exclude(notification_type__isnull=True)
        return queryset

class ChatNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset= Notification.objects.filter(
            recipient=self.request.user,
            notification_type__iexact="chat"
        ).order_by('-created_at')
        return queryset

class GroupChatNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            notification_type="group_chat"
        ).order_by('-created_at')

# specific notification
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

# all notification       
class MarkAllNotificationsAsRead(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        updated_count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"message": f"{updated_count} notifications marked as read"}, status=status.HTTP_200_OK)


# delete specific notification 
class DeleteNotification(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, notification_id):
        deleted_count, _ = Notification.objects.filter(id=notification_id, recipient=request.user).delete()
        if deleted_count == 0:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Notification deleted"}, status=status.HTTP_200_OK)

# delete all notification 
class ClearAllNotifications(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = Notification.objects.filter(recipient=request.user).delete()
        return Response({"message": f"{deleted_count} notifications deleted"}, status=status.HTTP_200_OK)


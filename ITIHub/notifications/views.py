from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

        # Allow filtering by notification type
        notification_type = self.request.query_params.get('type', '').strip()
        if notification_type:
            queryset = queryset.filter(notification_type__iexact=notification_type)
        
        return queryset.select_related("sender").prefetch_related("recipient")  # Optimize DB queries

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

class MarkAllNotificationsAsRead(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        updated_count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"message": f"{updated_count} notifications marked as read"}, status=status.HTTP_200_OK)

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
        deleted_count, _ = Notification.objects.filter(recipient=request.user).delete()
        return Response({"message": f"{deleted_count} notifications deleted"}, status=status.HTTP_200_OK)

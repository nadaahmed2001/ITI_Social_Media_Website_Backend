from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    notification_text = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'notification_type', 'created_at', 'is_read', 'status', 'notification_text']

    def get_sender(self, obj):
        return {"id": obj.sender.id, "username": obj.sender.username} if obj.sender else None

    def get_status(self, obj):
        return "read" if obj.is_read else "unread"

    def get_notification_text(self, obj):
        if obj.notification_type == "chat":
            return f"New message from {obj.sender.username}"
        elif obj.notification_type == "group_chat":
            return f"New message in a group chat"
        elif obj.notification_type == "mention":
            return f"You were mentioned by {obj.sender.username}"
        elif obj.notification_type == "batch_assignment":
            return "You have been assigned to a new batch"
        return "New notification"

from rest_framework import serializers
from .models import Notification
from chat.models import ChatMessage, GroupMessage
from django.urls import reverse

class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    message_content = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    notification_text = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'

    def get_related_message(self, obj):        
        model = ChatMessage if obj.notification_type == "chat" else GroupMessage
        return model.objects.select_related("sender").filter(id=obj.related_object_id).first()

    def get_sender(self, obj):
        message = self.get_related_message(obj)
        return {"id": message.sender.id, "username": message.sender.username} if message else None

    def get_message_content(self, obj):
        message = self.get_related_message(obj)
        if message:
            return message.message if obj.notification_type == "chat" else message.content
        return None
    
    def get_group_name(self, obj):
        message = self.get_related_message(obj)
        return message.group.name if message and hasattr(message, "group") else None

    def get_status(self, obj):
        return "read" if obj.is_read else "unread"

    def get_notification_text(self, obj):
        message = self.get_related_message(obj)
        if message:
            if obj.notification_type == "chat":
                return f"New message from {message.sender.username}"
            elif obj.notification_type == "group_chat":
                return f"New message in {message.group.name} from {message.sender.username}"
        return "New notification"

    def get_chat_or_group_url(self, obj):
        if obj.notification_type == "group_chat":
            message = self.get_related_message(obj)
            if message and hasattr(message, "group"):
                return reverse("group-detail", kwargs={"group_id": message.group.id})
        return None

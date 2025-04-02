from rest_framework import serializers
from django.urls import reverse
from .models import Notification
from chat.models import ChatMessage, GroupMessage
from batches.models import Batch
from posts.models import Post, Comment  

class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    notification_text = serializers.SerializerMethodField()
    notification_link = serializers.SerializerMethodField()
    reaction_type = serializers.CharField(source="get_reaction_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'notification_type', 'reaction_type', 'created_at',
            'is_read', 'status', 'notification_text', 'notification_link'
        ]

    def get_sender(self, obj):
        return {"id": obj.sender.id, "username": obj.sender.username} if obj.sender else None

    def get_status(self, obj):
        return "read" if obj.is_read else "unread"

    def get_related_object(self, obj):
        model_map = {
            "chat": ChatMessage,
            "group_chat": GroupMessage,
            "batch_assignment": Batch,
            "batch_end": Batch,
            "reaction": Post,
            "comment": Comment,
        }
        model = model_map.get(obj.notification_type)
        return model.objects.filter(id=obj.related_object_id).select_related().first() if model else None

    def get_notification_text(self, obj):
        related_object = self.get_related_object(obj)
        sender_username = getattr(obj.sender, "username", "Someone")

        if obj.notification_type == "chat":
            return f"New message from {related_object.sender.username}" if related_object else "New message"

        elif obj.notification_type == "group_chat":
            group_name = related_object.group.name if related_object and related_object.group else "a group chat"
            return f"New message in {group_name}"

        elif obj.notification_type == "mention":
            return f"You were mentioned by {sender_username}"

        elif obj.notification_type == "batch_assignment":
            return f"You have been assigned to the batch {related_object.name}" if related_object else "You have been assigned to a batch"

        elif obj.notification_type == "batch_end":
            return f"The batch {related_object.name} has ended" if related_object else "Your batch has ended"

        elif obj.notification_type == "reaction":
            reaction_type = getattr(obj, "reaction_type", None)
            if reaction_type:
                return f"{sender_username} {reaction_type}d your post"
            return f"{sender_username} reacted to your post"

        return "New notification"



    def get_notification_link(self, obj):
        related_object = self.get_related_object(obj)

        if obj.notification_type == "batch_assignment" and related_object:
            return reverse("batch-detail", kwargs={"batch_id": related_object.id})

        elif obj.notification_type in ["reaction", "comment"] and related_object:
            return reverse("post-detail", kwargs={"post_id": related_object.id})

        elif obj.notification_type == "follow":
            return reverse("user-profile", kwargs={"username": obj.sender.username})

        return None

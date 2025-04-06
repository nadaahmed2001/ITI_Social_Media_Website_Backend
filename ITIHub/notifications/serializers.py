from rest_framework import serializers
from django.urls import reverse
from .models import Notification
from chat.models import ChatMessage, GroupMessage
from batches.models import Batch
from posts.models import Post, Comment, Reaction
from django.conf import settings



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
            "reaction": Reaction,  # Ensure Reaction is handled correctly
            "comment": Comment,
        }
        model = model_map.get(obj.notification_type)
        return model.objects.filter(id=obj.related_object_id).first() if model else None

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

        elif obj.notification_type == "comment":
            comment_text = related_object.comment if related_object else "your post"
            comment_author = related_object.author.username if related_object else "Unknown"
            return f"{comment_author} commented on your post: '{comment_text}'"

        return "New notification"

    def get_notification_link(self, obj):
        related_object = self.get_related_object(obj)
        base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")

        if obj.notification_type == "batch_assignment" and related_object:
            return f"{base_url}/batches/{related_object.id}/"

        elif obj.notification_type in ["reaction", "comment"] and related_object:
            # Handle the correct link for reactions and comments
            if obj.notification_type == "reaction":
                return f"{base_url}/posts/{related_object.post.id}/reaction-{related_object.id}"
            elif obj.notification_type == "comment":
                return f"{base_url}/posts/{related_object.post.id}/comment-{related_object.id}"
            return f"{base_url}/posts/{related_object.post.id}/"

        elif obj.notification_type == "follow":
            return f"{base_url}/profile/{obj.sender.username}/"

        return f"{base_url}/"  # Default fallback to homepage

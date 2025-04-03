from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reaction', 'Reaction'),
        ('comment', 'Comment'),
        ('new_post', 'New Post'),
        ('mention', 'Mention'),
        ('message', 'Message'),
        ('chat', 'Chat'),
        ('group_chat', 'Group Chat'),
        ('follow', 'Follow'),
        ('batch_assignment', 'Batch Assignment'),
        ('batch_end', 'Batch End'),
    ]

    REACTION_TYPES = [
        ("like", "Like"),
        ("love", "Love"),
        ("haha", "Haha"),
        ("wow", "Wow"),
        ("sad", "Sad"),
        ("angry", "Angry"),
    ]


    recipient = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_notifications", on_delete=models.SET_NULL, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    related_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('related_content_type', 'related_object_id')

    def __str__(self):
        return f"{self.recipient.username} - {self.get_notification_type_display()}"

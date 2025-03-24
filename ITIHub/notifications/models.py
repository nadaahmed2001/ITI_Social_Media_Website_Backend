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

    recipient = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_notifications", on_delete=models.SET_NULL, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    related_object_id = models.PositiveIntegerField(null=True, blank=True, default=None) 
    def __str__(self):
        return f"{self.recipient.username} - {self.get_notification_type_display()}"

from django.db import models
from batches.models import Batch
from users.models import User

# Create your models here.
class GroupChat(models.Model):
    group_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE, null=True, blank=True)
    group_chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

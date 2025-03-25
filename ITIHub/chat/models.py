from django.db import models
from django.conf import settings  # Import settings to reference AUTH_USER_MODEL

class GroupChat(models.Model):
    name = models.CharField(max_length=255, unique=True, blank=False, default='Group')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_members')
    supervisors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_supervisors')

    def __str__(self):
        return self.name

class GroupMessage(models.Model):
    group = models.ForeignKey(GroupChat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:20]}'

class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE, null=True, blank=True)
    group_chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.message[:20]}'

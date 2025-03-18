from django.db import models
from users.models import User
from batches.models import Department

# Create your models here.
class Post(models.Model):
    CATEGORY_CHOICES = [
        ('Discussion', 'Discussion'),
        ('Event', 'Event'),
        ('Question', 'Question'),
        ('Resource', 'Resource'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    attachment = models.ForeignKey('Attachment', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey(Department, on_delete=models.CASCADE)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Reaction(models.Model):
    REACTIONS = [
        ('Like', 'Like'),
        ('Heart', 'Heart'),
        ('Clap', 'Clap'),
        ('Laugh', 'Laugh'),
        ('Support', 'Support'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

class Attachment(models.Model):
    image = models.ImageField(upload_to="attachments/", null=True, blank=True)
    video = models.FileField(upload_to="attachments/", null=True, blank=True)

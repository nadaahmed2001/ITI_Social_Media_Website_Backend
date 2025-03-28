from django.db import models
from django.utils import timezone
from users.models import User
from batches.models import Department
from django.db import models
from django.utils import timezone

class Attachment(models.Model):
    image = models.ImageField(upload_to="attachments/", null=True, blank=True)
    video = models.FileField(upload_to="attachments/", null=True, blank=True)
    uploaded_on = models.DateTimeField( default=timezone.now) 

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    body = models.TextField()
    created_on = models.DateTimeField(default=timezone.now) 
    attachments = models.ManyToManyField(Attachment, blank=True)  

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    attachments = models.ManyToManyField(Attachment, blank=True)  

class Reaction(models.Model):
    REACTIONS = [
        ('Like', 'Like'),
        ('Heart', 'Heart'),
        ('Celebrate', 'Celebrate'),
        ('Laugh', 'Laugh'),
        ('Insightful', 'Insightful'),
        ('Support', 'Support'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)  # Modified
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    reaction_type = models.CharField(max_length=20, choices=REACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'post', 'comment')  

    def __str__(self):
        return f"{self.user} reacted {self.reaction_type}"
    


from django.db import models
from django.utils import timezone
from users.models import User
from batches.models import Department

# Create your models here.
class Post(models.Model):
    attachment = models.ForeignKey('Attachment', on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateTimeField(default=timezone.now) 
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    likes = models.ManyToManyField(User,blank=True,related_name='likes')
    dislike = models.ManyToManyField(User,blank=True,related_name='dislikes')

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE , null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True) 

# # class Reaction(models.Model):
#     REACTIONS_TYPES = [
#         ('Like', 'Like'),
#         ('Heart', 'Heart'),
#         ('Clap', 'Clap'),
#         ('Laugh', 'Laugh'),
#         ('Support', 'Support'),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(Post, on_delete=models.CASCADE , related_name='reactions')
#     reaction_type = models.CharField(max_length=10, choices=REACTIONS_TYPES)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'post')  

#     # def __str__(self):
#     #     return f"{self.user} reacted {self.reaction_type} on {self.post.id}"
    

class Attachment(models.Model):
    image = models.ImageField(upload_to="attachments/", null=True, blank=True)
    video = models.FileField(upload_to="attachments/", null=True, blank=True)

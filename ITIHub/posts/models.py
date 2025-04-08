from django.db import models
from django.utils import timezone
from users.models import User

class Attachment(models.Model):
    # Store the Cloudinary URL directly
    url = models.URLField(default='https://res.cloudinary.com/dsaznefnt/image/upload/v1744085023/post_attachments/xd7a2ji9dqjvnb5mrjup.png', max_length=500)
    resource_type = models.CharField(max_length=20, default='image', choices=(('image', 'Image'), ('video', 'Video'), ('raw', 'Raw'))) # Added choices
    uploaded_on = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.resource_type.capitalize()} Attachment ({self.id})"
    

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    body = models.TextField(max_length=2500)
    created_on = models.DateTimeField(default=timezone.now)
    attachments = models.ManyToManyField(Attachment, blank=True)

    def _str_(self):
        return f"Post by {self.author} on {self.created_on}"

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    attachments = models.ManyToManyField(Attachment, blank=True)

    def _str_(self):
        return f"Comment by {self.author} on {self.post}"

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}

class Reaction(models.Model):
    REACTIONS = [
        ('Like', 'Like'),
        ('Love', 'Love'),
        ('Celebrate', 'Celebrate'),
        ('Funny', 'funny'),
        ('Insightful', 'Insightful'),
        ('Support', 'Support'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    reaction_type = models.CharField(max_length=10, choices=REACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post', 'comment')

    def _str_(self):
        target = self.post if self.post else self.comment
        return f"{self.user} reacted {self.reaction_type} on {target}"
    
class Reply(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
    parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='threads')
    body = models.TextField()
    attachments = models.ManyToManyField(Attachment, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() 
                for reaction, _ in Reaction.REACTIONS}

    def __str__(self):
        return f"Reply by {self.author} on {self.created_on}"
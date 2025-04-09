from django.db import models
from django.utils import timezone
from users.models import User
from django.core.validators import MaxLengthValidator, MinLengthValidator

# models.py
class Attachment(models.Model):
    image = models.URLField(null=True, blank=True)  # Changed from ImageField to URLField
    video = models.URLField(null=True, blank=True)  # Changed from FileField to URLField
    uploaded_on = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Attachment {self.id}"
    
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    body = models.TextField(validators=[MaxLengthValidator(3000), MinLengthValidator(1)])
    created_on = models.DateTimeField(default=timezone.now)
    attachments = models.ManyToManyField(Attachment, blank=True)

    def _str_(self):
        return f"Post by {self.author} on {self.created_on}"

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}
    
    class Meta:
        ordering = ['-created_on']

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(validators=[MaxLengthValidator(3000), MinLengthValidator(1)])
    created_on = models.DateTimeField(auto_now_add=True)
    attachments = models.ManyToManyField(Attachment, blank=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post}"

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}

class Reaction(models.Model):
    REACTIONS = [
        ('Like', 'Like'),
        ('Love', 'Love'),
        ('Celebrate', 'Celebrate'),
        ('funny', 'funny'),
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
# from django.db import models
# from django.utils import timezone
# from users.models import User
# import uuid
# from django.db.models.functions import Lower


# class Attachment(models.Model):
#     # Store the Cloudinary URL directly
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Added UUID PK
#     url = models.URLField(default='https://res.cloudinary.com/dsaznefnt/image/upload/v1744085023/post_attachments/xd7a2ji9dqjvnb5mrjup.png', max_length=500)
#     resource_type = models.CharField(max_length=20, default='image', choices=(('image', 'Image'), ('video', 'Video'), ('raw', 'Raw')))
#     uploaded_on = models.DateTimeField(default=timezone.now)
    
#     def __str__(self):
#         return f"{self.resource_type.capitalize()} Attachment ({self.id})"


# class Reaction(models.Model):
#     REACTIONS = [
#         ('Like', 'Like'), ('Love', 'Love'), ('Celebrate', 'Celebrate'),
#         ('Funny', 'Funny'), ('Insightful', 'Insightful'), ('Support', 'Support'), # Consistent Caps
#     ]
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Added UUID PK
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True, related_name='reaction_set') # Use string reference
#     comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='reaction_set') # Use string reference
#     reaction_type = models.CharField(max_length=15, choices=REACTIONS) # Increased length
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'post', 'comment')

#     def __str__(self):
#         target_str = "target"
#         if self.post: target_str = f"Post {self.post_id}"
#         elif self.comment: target_str = f"Comment {self.comment_id}"
#         return f"{self.user.username if self.user else 'User'} reacted {self.reaction_type} on {target_str}"


# class Post(models.Model):
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Added UUID PK
#     author = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
#     body = models.TextField(max_length=2500)
#     created_on = models.DateTimeField(default=timezone.now)
#     attachments = models.ManyToManyField(Attachment, blank=True)

#     def __str__(self): # Corrected method name
#         return f"Post ({self.id}) by {self.author.username if self.author else 'Unknown'}"

#     def reaction_counts(self):
#         return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}

# class Comment(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Added UUID PK

#     author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE, null=False)
#     post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
#     comment = models.TextField(max_length=1500) # Add max length validation
#     created_on = models.DateTimeField(auto_now_add=True)
#     attachments = models.ManyToManyField(Attachment, blank=True)

#     def _str_(self):
#         return f"Comment by {self.author} on {self.post}"

#     def reaction_counts(self):
#         return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}
    
# class Reply(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Added UUID PK
#     author = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
#     comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
#     parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='threads')
#     body = models.TextField(max_length=1500) # Add max length
#     attachments = models.ManyToManyField(Attachment, blank=True)
#     created_on = models.DateTimeField(auto_now_add=True)

#     def reaction_counts(self):
#         return {reaction: self.reaction_set.filter(reaction_type=reaction).count() 
#                 for reaction, _ in Reaction.REACTIONS}

#     def __str__(self):
#         return f"Reply by {self.author} on {self.created_on}"

# posts/models.py
from django.db import models
from django.utils import timezone
from users.models import User # Adjust import if needed
import uuid
from django.db.models.functions import Lower

# Attachment model stores URLs from Cloudinary
class Attachment(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=550) # Store Cloudinary URL
    resource_type = models.CharField(max_length=20, default='image', choices=(('image', 'Image'), ('video', 'Video'), ('raw', 'Raw')))
    uploaded_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.resource_type.capitalize()} Attachment ({self.id})"

# Define Reaction model first if needed by methods below
class Reaction(models.Model):
    REACTIONS = [
        ('Like', 'Like'), ('Love', 'Love'), ('Celebrate', 'Celebrate'),
        ('Funny', 'Funny'), ('Insightful', 'Insightful'), ('Support', 'Support'), # Consistent Caps
    ]
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Add related_name to avoid clashes
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True, related_name='reaction_set')
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='reaction_set')
    reaction_type = models.CharField(max_length=15, choices=REACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post', 'comment')
        ordering = ['-timestamp'] # Optional: order reactions

    def __str__(self):
        target_str = "target"
        if self.post: target_str = f"Post {self.post_id}"
        elif self.comment: target_str = f"Comment {self.comment_id}"
        return f"{self.user.username if self.user else 'User'} reacted {self.reaction_type} on {target_str}"

class Post(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE) # Added related_name
    body = models.TextField(max_length=2500)
    created_on = models.DateTimeField(default=timezone.now)
    attachments = models.ManyToManyField(Attachment, blank=True, related_name='posts') # Added related_name

    class Meta:
        ordering = ['-created_on'] # Default ordering

    def __str__(self): # Corrected method name
        return f"Post ({self.id}) by {self.author.username if self.author else 'Unknown'}"

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}

class Comment(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Ensure author cannot be null if required for comments
    author = models.ForeignKey(User, related_name='comments_made', on_delete=models.CASCADE) # Changed related_name
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(max_length=1500)
    created_on = models.DateTimeField(auto_now_add=True)
    attachments = models.ManyToManyField(Attachment, blank=True, related_name='comments') # Added related_name

    class Meta:
        ordering = ['created_on'] # Default ordering for comments (oldest first)

    def __str__(self): # Corrected method name
        return f"Comment ({self.id}) by {self.author.username if self.author else 'Unknown'}"

    def reaction_counts(self):
        return {reaction: self.reaction_set.filter(reaction_type=reaction).count() for reaction, _ in Reaction.REACTIONS}

class Reply(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, related_name='replies_made', on_delete=models.CASCADE) # Changed related_name
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
    parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_replies') # Changed related_name
    body = models.TextField(max_length=1500)
    attachments = models.ManyToManyField(Attachment, blank=True, related_name='replies') # Added related_name
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_on']

    # Reaction needs ForeignKey to Reply for this to work
    # def reaction_counts(self): return {}

    def __str__(self):
        return f"Reply ({self.id}) by {self.author.username if self.author else 'Unknown'}"
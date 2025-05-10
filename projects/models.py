from django.db import models
from django.db.models.functions import Lower
from users.models import Profile
import uuid
import pprint
from django.conf import settings

# Create your models here.
class Project(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    contributors = models.ManyToManyField(Profile, related_name='contributed_projects', blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    featured_image = models.URLField(max_length=500, null=True, blank=True)
    demo_link = models.CharField(max_length=2000,null= True , blank=True)
    source_link = models.CharField(max_length=2000,null= True , blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('Tag', related_name='tags', blank=True)
    
    # Optional helper methods
    @property
    def like_count(self):
        return self.projectlike_set.count() # Use default related name
    
    def __str__(self):
        return self.title
    

# Tags(skills) used in the project     
class Tag(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=100, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        # This is to make the name unique, case-insenstive
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                name='unique_lower_name',
            )
        ]
        
    def __str__(self):
        return self.name
    

class ProjectLike(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    # *** Like remains linked to User account ***
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_likes')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('user', 'project'); ordering = ['-created']
    def __str__(self): return f"{self.user.username} likes {self.project.title}"


class ProjectReview(models.Model):
    VOTE_TYPE = ( ('up', 'Up Vote'), ('down', 'Down Vote'), )
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    # *** CHANGE: Link reviewer directly to Profile ***
    reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='project_reviews') # Changed from User to Profile
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reviews')
    body = models.TextField(null=True, blank=True)
    vote = models.CharField(max_length=20, choices=VOTE_TYPE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        # *** CHANGE: unique_together now uses Profile (reviewer) ***
        unique_together = ('reviewer', 'project')
        ordering = ['-created']

    def __str__(self):
        # *** CHANGE: Access username via profile ***
        vote_str = f" ({self.get_vote_display()})" if self.vote else ""
        return f"Review for {self.project.title} by {self.reviewer.username}{vote_str}" # Assuming Profile has username


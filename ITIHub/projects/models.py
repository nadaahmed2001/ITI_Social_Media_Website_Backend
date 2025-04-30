from django.db import models
from django.db.models.functions import Lower
from users.models import Profile
import uuid


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
    """ Records a user liking a project. """
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True) # Link to Profile
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_likes')
    project = models.ForeignKey(Project, on_delete=models.CASCADE) # Default related_name is projectlike_set
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project') # User can like a project only once
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} likes {self.project.title}"


class ProjectReview(models.Model):
    """ Stores user reviews/comments on projects. """
    # Define vote choices if using up/down votes
    VOTE_TYPE = (
        ('up', 'Up Vote'),
        ('down', 'Down Vote'),
    )

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    # Consider using User directly if Profiles might not exist or if reviews are tied to the account
    reviewer = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True) # Link to Profile
    # reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # Link to User
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reviews')
    body = models.TextField(null=True, blank=True)
    # Use vote field instead of rating for simplicity now
    vote = models.CharField(max_length=20, choices=VOTE_TYPE, null=True, blank=True) # Allow null vote if just commenting
    # rating = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]) # Example for 1-5 rating
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        # User can review a project only once
        unique_together = ('reviewer', 'project')
        ordering = ['-created']

    def __str__(self):
        vote_str = f" ({self.get_vote_display()})" if self.vote else ""
        return f"Review for {self.project.title} by {self.reviewer.username}{vote_str}"

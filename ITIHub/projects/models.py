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
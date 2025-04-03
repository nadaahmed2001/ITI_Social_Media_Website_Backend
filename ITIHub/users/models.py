from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid
from django.conf import settings 
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    """
    Custom User model supporting both students and supervisors.
    - Role-based flags (`is_student`, `is_supervisor`) for easy permission checks.
    """
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    # Role-based flags
    is_student = models.BooleanField(default=False)
    is_supervisor = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)  # Account activation flag

    # Student-specific: National ID (only required for students)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # Fix for conflicts with Django’s default User model
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    def __str__(self):
        role = "Supervisor" if self.is_supervisor else "Student" if self.is_student else "User"
        return f"{self.username} ({role})"



class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)                 # One-to-one relationship between User and profile
    username = models.CharField(max_length=200, blank=True, null=True)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True) 
    email = models.EmailField(max_length=200, unique=True, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)   # import the default image  static -> images -> profiles -> user-default.png
    website_url = models.CharField(max_length=200, blank=True, null=True)  # portfolio_website
    twitter_url = models.CharField(max_length=200, blank=True, null=True)
    youtube_url = models.CharField(max_length=200, blank=True, null=True)
    github_url = models.CharField(max_length=200, blank=True, null=True)
    stackoverflow_url = models.CharField(max_length=200, blank=True, null=True)
    linkedin_url = models.CharField(max_length=100, blank=True, null=True)
    leetcode_username = models.CharField(max_length=100, blank=True, null=True)
    hackerrank_username = models.CharField(max_length=200, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.user.username)
    
    
class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return str(self.name)



class Follow(models.Model):
    """
    Follow system
    - Users can follow/unfollow each other.
    - Stored as `Many-to-Many` with timestamps.
    """
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # Prevents duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# Table to store the email change requests
class EmailChangeRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    new_email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=settings.EMAIL_CHANGE_EXPIRATION_HOURS or 1)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Email change request for {self.user.username} to {self.new_email}"
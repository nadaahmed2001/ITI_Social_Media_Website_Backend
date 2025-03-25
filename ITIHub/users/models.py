from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    """
    Custom User model supporting both students and supervisors.
    - Role-based flags (`is_student`, `is_supervisor`) for easy permission checks.
    """
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Role-based flags
    is_student = models.BooleanField(default=False)
    is_supervisor = models.BooleanField(default=False)

    is_active = models.BooleanField(default=False)  # Account activation flag

    # Student-specific: National ID (only required for students)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # Fix for conflicts with Django’s default User model
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    def __str__(self):
        role = "Supervisor" if self.is_supervisor else "Student" if self.is_student else "User"
        return f"{self.username} ({role})"



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

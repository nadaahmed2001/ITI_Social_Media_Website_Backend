from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser): 
    phone = models.CharField(max_length=50, unique=True)
    profile_picture = models.CharField(max_length=50, blank=True, null=True)
    # department = models.ForeignKey('batches.Department', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Fix for conflicts with Django’s default User model
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    def __str__(self):
        return self.username


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    batch = models.ForeignKey('batches.Batch', on_delete=models.SET_NULL, null=True)
    national_id = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Graduated', 'Graduated')])

class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    national_id = models.CharField(max_length=20, unique=True)

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

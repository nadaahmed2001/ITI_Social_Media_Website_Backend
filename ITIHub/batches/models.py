from django.conf import settings
from django.db import models
from django.utils.timezone import now
from chat.models import GroupChat  # Import the GroupChat model from the chat app

class Department(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branch_name = models.CharField(max_length=100)

class Program(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

class Track(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    # department = models.ForeignKey(Department, on_delete=models.CASCADE)


class Batch(models.Model):
    name = models.CharField(max_length=255)
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="supervised_batches"
    )
    program = models.ForeignKey(Program, on_delete=models.CASCADE)  # Link to Program
    track = models.ForeignKey(Track, on_delete=models.CASCADE)  # Link to Track
    created_at = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        # Check if batch is new
        is_new = self.pk is None  
        super().save(*args, **kwargs)

        if is_new:
            # Create a group chat for the batch with the supervisor as the admin
            group_chat = GroupChat.objects.create(name=f"Batch {self.name} Chat")
            group_chat.supervisors.add(self.supervisor)  # Add supervisor as admin

    def __str__(self):
        return f"{self.name} - {self.track.name} - {self.program.name}"


class Student(models.Model):
    """
    Student model that extends User.
    - Students are linked to batches via `StudentBatch`.
    - `status` helps track active vs. graduated students.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Graduated', 'Graduated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.user.username}"

class StudentBatch(models.Model):
    """
    Intermediate table to link Students to Batches.
    - A student can belong to multiple batches over time.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.batch.name}"
    
    
class UnverifiedNationalID(models.Model):
    """
    Stores national IDs uploaded by the supervisor before students register.
    """
    national_id = models.CharField(max_length=20, unique=True)
    batch = models.ForeignKey("Batch", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.national_id} - {self.batch.name}"

class VerifiedNationalID(models.Model):
    """
    Stores national IDs of registered students.
    """
    national_id = models.CharField(max_length=20, unique=True)
    batch = models.ForeignKey("Batch", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.national_id} - Verified"


from django.conf import settings
from django.db import models

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
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

class Batch(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Ended', 'Ended')])
    name = models.CharField(max_length=100)

class UnverifiedNationalID(models.Model):
    """
    Stores national IDs uploaded by the supervisor before students register.
    """
    national_id = models.CharField(max_length=20, unique=True)
    batch = models.ForeignKey("Batch", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.national_id} - {self.batch.name}"

class VerifiedNationalID(models.Model):
    national_id = models.CharField(max_length=20, unique=True)
    batch = models.ForeignKey("Batch", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.national_id} - Verified"

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

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

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_student': True})
    national_id = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    
    
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

class StudentBatch(models.Model):
    """
    Links students to batches.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_student': True})
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.batch.name}"

from django.db import models
from users.models import Supervisor

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    supervisor = models.ForeignKey(Supervisor, on_delete=models.SET_NULL, null=True)
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
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    # list of students in the batch (list of national ids extracted from a csv file)
    students = models.TextField() #TextField is datatype for long text
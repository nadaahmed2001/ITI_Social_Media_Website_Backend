from django.contrib import admin


# Register your models here.
from .models import Department, Program, Track, Batch, Student, UnverifiedNationalID,StudentBatch,VerifiedNationalID

admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Track)
admin.site.register(Batch)
admin.site.register(Student)
admin.site.register(UnverifiedNationalID)
admin.site.register(StudentBatch)
admin.site.register(VerifiedNationalID)

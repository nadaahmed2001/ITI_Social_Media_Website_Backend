from django.contrib import admin

# Register your models here.
from .models import Department, Program, Track, Batch

admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Track)
admin.site.register(Batch)

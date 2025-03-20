from django.contrib import admin
from .models import User, Student, Supervisor, Follow
# Register your models here.
admin.site.register(User)
admin.site.register(Student)
admin.site.register(Supervisor)
admin.site.register(Follow)

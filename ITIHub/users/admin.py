from django.contrib import admin
from .models import User, Follow, Profile, Skill
# Register your models here.
admin.site.register(User)
admin.site.register(Follow)


# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'username')

    def name(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name

admin.site.register(Profile, ProfileAdmin)


class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'owner')

admin.site.register(Skill, SkillAdmin)



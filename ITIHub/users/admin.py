from django.contrib import admin
from .models import User, Follow, Profile, Skill
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'is_student', 'is_supervisor')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ['username', 'email', 'is_student', 'is_supervisor', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'national_id', 'is_student', 'is_supervisor', 'is_two_factor_enabled')}),
    )

admin.site.register(User, CustomUserAdmin)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'username')

    def name(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name

admin.site.register(Profile, ProfileAdmin)


class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'owner')

admin.site.register(Skill, SkillAdmin)



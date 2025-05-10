from django.contrib import admin
from .models import User, Follow, Profile, Skill
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.hashers import make_password


class CustomUserAdmin(BaseUserAdmin):
    # Specify the fields to display in the admin panel
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'national_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Roles', {'fields': ('is_student', 'is_supervisor')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields to display when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'phone', 'national_id', 'is_student', 'is_supervisor'),
        }),
    )

    # Fields to display in the list view
    list_display = ('username', 'email', 'is_student', 'is_supervisor', 'is_active')
    list_filter = ('is_student', 'is_supervisor', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone', 'national_id')
    ordering = ('username',)

    def save_model(self, request, obj, form, change):
        # Hash the password if it's being set or changed
        if form.cleaned_data.get("password"):
            obj.password = make_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)


# Register the custom UserAdmin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Follow)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'username')

    def name(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name


admin.site.register(Profile, ProfileAdmin)


class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'owner')


admin.site.register(Skill, SkillAdmin)
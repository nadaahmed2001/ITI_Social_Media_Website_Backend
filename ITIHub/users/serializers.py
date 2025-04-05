from rest_framework import serializers
from .models import User
from batches.models import StudentBatch
from users.models import Profile, Skill
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "is_student", "is_supervisor"]

class RegisterStudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "national_id"]

    def create(self, validated_data):
        validated_data["is_student"] = True
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)



class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.URLField(max_length=500, required=False, allow_null=True)
    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ['user', 'created', 'updated'] # User link shouldn't be changed via this serializer



class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        
        

User = get_user_model() # Use your custom User model

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        """
        Check if the current password provided matches the user's actual password.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct.")
        return value

    def validate_new_password(self, value):
        """
        Validate the new password against Django's password validators.
        """
        try:
            password_validation.validate_password(value, self.context['request'].user)
        except DjangoValidationError as e:
            # Raise DRF validation error from Django's validation error messages
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        """
        Check that new passwords match and are different from the current one.
        """
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords must match."})

        # Check if new password is same as old one (optional but good practice)
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the current password."})

        return data

class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    confirm_new_email = serializers.EmailField(required=True, write_only=True)
    current_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'}) # Require password to change email

    def validate_current_password(self, value):
        """
        Check current password for authorization.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct for authorization.")
        return value

    def validate_new_email(self, value):
        """
        Check if the new email is already in use by another user.
        """
        user = self.context['request'].user
        new_email = value.lower().strip() # Normalize email

        # Check if it's the same as the current email
        if new_email == user.email.lower():
            raise serializers.ValidationError("New email cannot be the same as the current email.")

        # Check if another user already has this email
        if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email address is already in use by another account.")
        return new_email # Return normalized email

    def validate(self, data):
        """
        Check that new emails match.
        """
        if data['new_email'].lower() != data['confirm_new_email'].lower():
            raise serializers.ValidationError({"confirm_new_email": "New email addresses must match."})
        return data
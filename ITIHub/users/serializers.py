from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from batches.models import StudentBatch
from users.models import Profile, Skill
from django.contrib.auth.tokens import default_token_generator

class AuthorSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying basic author information
    (id, username, name, profile picture) nested within other objects.
    """
    # Access the 'profile_picture' field from the related Profile model
    # using the default reverse accessor 'profile'.
    # Assumes 'profile_picture' field on Profile model stores the full URL.
    # Use URLField as the backend model stores the URL string now.
    profile_picture = serializers.URLField(source='profile.profile_picture', read_only=True, allow_null=True)
    # Alternatively, if profile_picture on Profile is still an ImageField managed by
    # Cloudinary storage, use ImageField here:
    # profile_picture = serializers.ImageField(source='profile.profile_picture', read_only=True, use_url=True, allow_null=True)

    class Meta:
        model = User
        # Specify fields to include for the author representation
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'profile_picture', # The field fetching the URL from Profile
        ]
        read_only = True # Make all fields read-only by default for this serializer


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
        read_only_fields = ['user', 'created', 'updated']



class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        

#reset password serializers
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

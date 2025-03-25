from rest_framework import serializers
from .models import User
from batches.models import StudentBatch

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "profile_picture", "is_student", "is_supervisor"]

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

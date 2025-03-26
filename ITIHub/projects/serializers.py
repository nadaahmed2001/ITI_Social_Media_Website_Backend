from rest_framework import serializers
from projects.models import Project, Tag
from users.models import Profile


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"

class ProjectSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for 'owner' to accept a UUID for the Profile
    owner = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all())
    
    # Serialize tags as usual
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Project
        fields = "__all__"

    def validate_title(self, value):
        # Example validation: Ensure title is not blank
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty or just whitespace.")
        return value

    def validate(self, data):
    # Access the request context to get the logged-in user
        user = self.context['request'].user.profile
        
        # Perform a case-insensitive check for the title
        if Project.objects.filter(owner=user, title__iexact=data['title']).exists():
            raise serializers.ValidationError("You already have a project with this title.")
        
        return data
                
class ContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username']  # You can add other fields like first_name, last_name, etc.
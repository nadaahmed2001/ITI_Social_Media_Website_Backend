from rest_framework import serializers
from projects.models import Project, Tag
from users.models import Profile


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"

# class ProjectSerializer(serializers.ModelSerializer):
#     # Use PrimaryKeyRelatedField for 'owner' to accept a UUID for the Profile
#     owner = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all())
    
#     # Serialize tags as usual
#     tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)

#     class Meta:
#         model = Project
#         fields = "__all__"

#     def validate_title(self, value):
#         # Example validation: Ensure title is not blank
#         if not value.strip():
#             raise serializers.ValidationError("Title cannot be empty or just whitespace.")
#         return value

#     def validate(self, data):
#     # Access the request context to get the logged-in user
#         user = self.context['request'].user.profile
        
#         # Perform a case-insensitive check for the title
#         if Project.objects.filter(owner=user, title__iexact=data['title']).exists():
#             raise serializers.ValidationError("You already have a project with this title.")
        
#         return data
                
# class ContributorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ['id', 'username']  # You can add other fields like first_name, last_name, etc.

class ContributorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'profile_image']

class ProjectSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for 'owner' during write operations
    # Consider adding read_only nested serializer for owner details during reads if needed
    owner = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all())

    # Keep tags as PrimaryKeyRelatedField for writes, maybe add nested read serializer
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False) # Make tags not strictly required

    # If you added nested contributors for reading:
    contributors = ContributorProfileSerializer(many=True, read_only=True)
    # If you added featured_image:
    featured_image = serializers.ImageField(read_only=True, required=False)

    class Meta:
        model = Project
        # Explicitly list fields
        fields = [
            'id', 'owner', 'title', 'description', 'demo_link',
            'source_link', 'created', 'modified', 'tags',
            'contributors', 'featured_image' # Ensure all needed fields are here
        ]
        # Fields that are populated automatically or managed separately
        read_only_fields = ['contributors', 'created', 'modified']


    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty or just whitespace.")
        return value

    # --- CORRECTED VALIDATE METHOD ---
    def validate(self, data):
        # Only perform the title uniqueness check if the title is actually present in the input data
        # This prevents errors during partial updates where title isn't provided
        if 'title' in data:
            user_profile = self.context['request'].user.profile
            title = data['title']

            # Base queryset for checking title uniqueness
            queryset = Project.objects.filter(owner=user_profile, title__iexact=title)

            # If self.instance exists, we are *updating* an existing project
            if self.instance:
                # Exclude the current project instance from the uniqueness check
                queryset = queryset.exclude(pk=self.instance.pk)

            # Now check if any *other* project exists with this title for this user
            if queryset.exists():
                # Raise a field-specific error for better frontend handling
                raise serializers.ValidationError({
                    "title": "You already have another project with this title."
                })
        # --- END OF CORRECTION ---

        # You can add other cross-field validations here if needed

        return data
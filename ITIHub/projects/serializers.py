from rest_framework import serializers
from projects.models import Project, Tag
from users.models import Profile


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


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
    featured_image = serializers.ImageField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = Project
        fields = [
            'id', 'owner', 'title', 'description', 'demo_link',
            'source_link', 'created', 'modified', 'tags',
            'contributors', 'featured_image' 
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


# ==============================================================================================================================================

# from rest_framework import serializers
# from projects.models import Project, Tag
# from users.models import Profile # Assuming Profile is in users.models
# from django.db import transaction # Import transaction

# # Simple TagSerializer for reading nested data
# class TagSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Tag
#         fields = ['id', 'name']
#         read_only = True # Tags are usually managed via get_or_create, not direct creation here

# # Simple Profile Serializer for reading contributor/owner details
# class ContributorProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ['id', 'username', 'profile_image'] # Ensure profile_image gives URL via Cloudinary
#         read_only = True

# class ProjectSerializer(serializers.ModelSerializer):
#     # --- Read-only fields for GET responses ---
#     # Display full owner details on read
#     owner = ContributorProfileSerializer(read_only=True)
#     # Display full tag details on read (uses the 'tags' relationship)
#     tags = TagSerializer(many=True, read_only=True)
#     # Display full contributor details on read
#     contributors = ContributorProfileSerializer(many=True, read_only=True)
#     # Display Cloudinary URL for the image on read
#     featured_image = serializers.ImageField(read_only=True)

#     # --- Write-only fields for POST/PUT/PATCH ---
#     # Accept a list of tag *names* during create/update
#     tag_names = serializers.ListField(
#         child=serializers.CharField(max_length=100, allow_blank=False),
#         write_only=True,
#         required=False # Tags are optional
#     )
#     # Accept an image file upload during create/update
#     # 'source' links this write-only field to the actual model field 'featured_image'
#     featured_image_upload = serializers.ImageField(
#         write_only=True,
#         required=False, # Image is optional
#         allow_null=True, # Allow explicitly setting to null (or empty string for clearing)
#         source='featured_image'
#     )

#     class Meta:
#         model = Project
#         # Fields included in the API representation (both read and write sources)
#         fields = [
#             'id',
#             'owner', # Read-only nested data
#             'title',
#             'description',
#             'demo_link',
#             'source_link',
#             'featured_image', # Read-only URL
#             'tags',           # Read-only nested data
#             'contributors',   # Read-only nested data
#             'created',
#             'modified',
#             # Write-only fields (won't appear in response, used for input)
#             'tag_names',
#             'featured_image_upload',
#         ]
#         # Fields that are never expected as input or set automatically/in view
#         read_only_fields = ['created', 'modified'] # Owner is set via save()

#     def _handle_tags(self, instance, tag_names):
#         """Helper to get or create tags from names and set them on the instance."""
#         if not isinstance(tag_names, list): # Should be a list from ListField
#              return # Or raise validation error if needed
#         tags_to_set = []
#         for name in tag_names:
#             name_stripped = name.strip()
#             if name_stripped: # Avoid empty tags
#                 # Case-insensitive get_or_create
#                 tag, created = Tag.objects.get_or_create(
#                     name__iexact=name_stripped,
#                     defaults={'name': name_stripped} # Save with the provided casing if created
#                 )
#                 tags_to_set.append(tag)
#         # Set the ManyToMany relationship
#         instance.tags.set(tags_to_set)

#     @transaction.atomic
#     def create(self, validated_data):
#         """Handle creation, including tags."""
#         # Pop the write-only tag_names list before creating the Project instance
#         tag_names = validated_data.pop('tag_names', []) # Default to empty list if not provided
#         # 'featured_image' (from 'featured_image_upload') is handled by ModelSerializer
#         # 'owner' is passed explicitly in the view: serializer.save(owner=...)
#         project = Project.objects.create(**validated_data)
#         # Handle tags after instance is created
#         self._handle_tags(project, tag_names)
#         return project

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         """Handle update, including tags if provided."""
#         # Pop tag_names if it's included in the update data (partial=True means it might not be)
#         tag_names = validated_data.pop('tag_names', None) # Use None to detect if field was sent

#         # 'featured_image' (from 'featured_image_upload') update is handled by ModelSerializer
#         # Note: If featured_image_upload is sent as "" or null, storage backend should handle clearing

#         # Update standard fields provided in validated_data
#         # ModelSerializer's default update does this, or manually:
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Update tags only if 'tag_names' was explicitly provided in the request data
#         if tag_names is not None: # Check if the key was present (even if empty list)
#             self._handle_tags(instance, tag_names)

#         return instance

#     # --- Keep Validation Methods ---
#     def validate_title(self, value):
#         if not value.strip():
#             raise serializers.ValidationError("Title cannot be empty or just whitespace.")
#         # Consider checking max_length here too if needed
#         return value

#     def validate(self, data):
#         """Corrected title uniqueness check for update vs create."""
#         if 'title' in data: # Only check if title is being potentially changed
#             user_profile = self.context['request'].user.profile
#             title = data['title']
#             queryset = Project.objects.filter(owner=user_profile, title__iexact=title)
#             if self.instance: # If updating
#                 queryset = queryset.exclude(pk=self.instance.pk)
#             if queryset.exists():
#                 raise serializers.ValidationError({
#                     "title": "You already have another project with this title."
#                 })
#         return data
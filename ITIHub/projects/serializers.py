from rest_framework import serializers
from projects.models import Project, Tag
from users.models import Profile
from django.db import transaction
import pprint


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class ContributorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'profile_picture']

class ProjectSerializer(serializers.ModelSerializer):
    owner = ContributorProfileSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True) # Reading existing tags
    contributors = ContributorProfileSerializer(many=True, read_only=True)
    featured_image = serializers.URLField(max_length=500, required=False, allow_null=True) # Assuming Widget approach (URL)

    # --- Write Fields ---
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank=False),
        write_only=True, required=False
    )
    

    class Meta:
        model = Project
        fields = [
            'id', 'owner', 'title', 'description', 'demo_link', 'source_link',
            'featured_image', 
            'tags',           
            'contributors',
            'created', 'modified',
            'tag_names',
        ]
        read_only_fields = ['owner', 'tags', 'contributors', 'created', 'modified']

    def _handle_tags(self, instance, tag_names):
        print(f"--- _handle_tags called for project {instance.id} ---") # DEBUG
        print(f"Received tag names list: {tag_names}") # DEBUG
        if not isinstance(tag_names, list):
            print("DEBUG: tag_names was not a list, returning.") # DEBUG
            return
        tags_to_set = []
        for name in tag_names:
            name_stripped = name.strip()
            if name_stripped:
                try:
                    tag, created = Tag.objects.get_or_create(
                        name__iexact=name_stripped, defaults={'name': name_stripped}
                    )
                    tags_to_set.append(tag)
                    print(f"DEBUG: Got/Created tag: {tag.name} (ID: {tag.id}), Created: {created}") # DEBUG
                except Exception as e:
                    print(f"ERROR during Tag.objects.get_or_create for '{name_stripped}': {e}") # DEBUG
            else:
                print(f"DEBUG: Skipping empty tag name.") # DEBUG

        try:
            print(f"DEBUG: Attempting instance.tags.set() with tags: {[t.id for t in tags_to_set]}") # DEBUG
            instance.tags.set(tags_to_set) # Set ManyToMany relationship
            print(f"DEBUG: instance.tags.set() executed successfully.") # DEBUG
        except Exception as e:
            print(f"ERROR during instance.tags.set(): {e}") # DEBUG
        print(f"--- _handle_tags finished for project {instance.id} ---") # DEBUG

    @transaction.atomic
    def create(self, validated_data):
        print("\n--- ProjectSerializer CREATE ---") # DEBUG
        print("Validated data BEFORE pop:") # DEBUG
        pprint.pprint(validated_data) # DEBUG

        tag_names = validated_data.pop('tag_names', []) # Pop tag_names
        print(f"Popped tag_names: {tag_names}") # DEBUG

        # Owner is passed via save(owner=...) from view
        # featured_image (URL string) is included in validated_data now
        print("Data passed to Project.objects.create:") # DEBUG
        pprint.pprint(validated_data) # DEBUG
        project = Project.objects.create(**validated_data)
        print(f"Project instance created with ID: {project.id}") # DEBUG

        self._handle_tags(project, tag_names) # Handle tags
        print("--- ProjectSerializer CREATE Finished ---") # DEBUG
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        print(f"\n--- ProjectSerializer UPDATE for Project ID: {instance.id} ---") # DEBUG
        print("Validated data BEFORE pop:") # DEBUG
        pprint.pprint(validated_data) # DEBUG

        # Pop tag_names if provided in the partial update data
        tag_names = validated_data.pop('tag_names', None)
        print(f"Popped tag_names: {tag_names}") # DEBUG

        # featured_image URL update handled by super().update
        print("Data passed to super().update:") # DEBUG
        pprint.pprint(validated_data) # DEBUG
        instance = super().update(instance, validated_data) # Update other fields
        print(f"Instance updated via super().") # DEBUG

        # Update tags only if tag_names key was present in the request
        if tag_names is not None:
            print("tag_names key was present, calling _handle_tags...") # DEBUG
            self._handle_tags(instance, tag_names)
        else:
            print("tag_names key was NOT present, skipping tag update.") # DEBUG

        print(f"--- ProjectSerializer UPDATE Finished for Project ID: {instance.id} ---") # DEBUG
        return instance
    
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty or just whitespace.")
        return value

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

            #  check if any *other* project exists with this title for this user
            if queryset.exists():
                # Raise a field-specific error for better frontend handling
                raise serializers.ValidationError({
                    "title": "You already have another project with this title."
                })
        

        return data


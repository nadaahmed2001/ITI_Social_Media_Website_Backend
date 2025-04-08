from rest_framework import serializers
from .models import Post, Comment, Attachment, Reaction, Reply
from users.models import User # Assuming User is in users app
from users.serializers import UserSerializer # For potentially embedding author details
from django.db import transaction
import mimetypes # For checking file types


class AuthorSerializer(serializers.ModelSerializer):
    # Assuming you have profile picture setup as per previous steps
    profile_picture = serializers.URLField(source='profile.profile_picture', read_only=True, allow_null=True) # Adjust source based on your Profile model field
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture']
        read_only = True

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
            model = Attachment
            fields = ['id', 'url', 'resource_type', 'uploaded_on'] # Returns url and type
            read_only_fields = ['id', 'uploaded_on']

class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True) # Read existing

    # Accept list of Cloudinary URLs on write
    attachments_input = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(max_length=500, allow_blank=True)), 
        write_only=True, required=False
    )
    
    class Meta:
        model = Post
        fields = [
            "id", "author", "body", "created_on",
            "reaction_counts", "attachments", # Read
            "attachments_input" # Write
        ]
        read_only_fields = ["id", "author", "created_on", "reaction_counts", "attachments", "attachment_input"]
    
    def validate_body(self, value):
        trimmed = value.strip()
        if len(trimmed) > 2500:
            raise serializers.ValidationError("Post cannot exceed 2500 characters")
        return trimmed

    


    def get_reaction_counts(self, obj): # Keep this
        return obj.reaction_counts() if hasattr(obj, 'reaction_counts') else {}

    def _handle_attachments_from_data(self, instance, attachments_data):
        print(f"--- _handle_attachments for post {instance.id} ---") # DEBUG
        print(f"Received attachments data list: {attachments_data}") # DEBUG
        if not isinstance(attachments_data, list): print("DEBUG: attachments_data not a list."); return
        new_attachment_ids = []
        for attach_data in attachments_data: # Iterate over dictionaries
            url = attach_data.get('url')
            resource_type = attach_data.get('resource_type', 'image') # Default to image if not provided
            print(f"Processing attachment data: url={url}, type={resource_type}") # DEBUG
            if url and isinstance(url, str):
                try:
                    attachment = Attachment.objects.create(url=url, resource_type=resource_type)
                    new_attachment_ids.append(attachment.id)
                    print(f"DEBUG: Created Attachment ID: {attachment.id}") # DEBUG
                except Exception as e:
                    print(f"ERROR creating attachment for {url}: {e}") # DEBUG
        if new_attachment_ids:
            try:
                print(f"DEBUG: Setting attachments for post {instance.id} with IDs: {new_attachment_ids}") # DEBUG
                instance.attachments.set(new_attachment_ids)
                print("DEBUG: instance.attachments.set() called.") # DEBUG
            except Exception as e:
                print(f"ERROR during instance.attachments.set(): {e}") # DEBUG
        else:
            print("DEBUG: No new attachment instances created/processed.") # DEBUG
        print(f"--- _handle_attachments finished ---") # DEBUG

    @transaction.atomic
    def create(self, validated_data):
        # Pop the list of URLs
        attachments_data = validated_data.pop('attachments_input', [])
        print(f"Popped 'attachments_input': {attachments_data}") # DEBUG        # Author passed from view
        post = Post.objects.create(**validated_data)
        print(f"Post instance created with ID: {post.id}") # DEBUG        # Create Attachment objects from URLs
        if attachments_data:
            print("Calling _handle_attachments_from_data...") # DEBUG
            self._handle_attachments_from_data(post, attachments_data)
        else:
            print("No attachments_input data found to process.") # DEBUG
        
        print("--- PostSerializer CREATE Finished ---") # DEBUG
        return post
    
    @transaction.atomic
    def update(self, instance, validated_data):
        attachments_data = validated_data.pop('attachments_input', None)
        instance = super().update(instance, validated_data) # Update body etc.
        if attachments_data is not None:
            instance.attachments.clear() # Consider deleting old Attachment objects too?
            self._handle_attachments_from_data(instance, attachments_data)
        return instance


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), write_only=True)

    attachments_input = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(max_length=500, allow_blank=True)),
        write_only=True, required=False
    )
    # Add post_id for writing, make post read-only or use AuthorSerializer

    class Meta:
        model = Comment
        fields = [
            "id", "post", "author", "comment", "created_on",
            "reaction_counts", "attachments", # Read
            "attachments_input" # Write - Ensure key matches
        ]
        read_only_fields = ["id", "author", "created_on", "reaction_counts", "attachments"]
        
    def validate_comment(self, value):
        trimmed = value.strip()
        if len(trimmed) > 1500:
            raise serializers.ValidationError("Comment cannot exceed 1500 characters")
        return trimmed

    

    def get_reaction_counts(self, obj): # Keep
        return obj.reaction_counts() if hasattr(obj, 'reaction_counts') else {}

    # Add helper or reuse logic
    def _handle_attachments_from_urls(self, instance, attachments_data):
        print(f"--- _handle_attachments for post {instance.id} ---") # DEBUG
        print(f"Received attachments data list: {attachments_data}") # DEBUG
        if not isinstance(attachments_data, list): print("DEBUG: attachments_data not a list."); return
        new_attachment_ids = []
        for attach_data in attachments_data: # Iterate over dictionaries
            url = attach_data.get('url')
            resource_type = attach_data.get('resource_type', 'image') # Default to image if not provided
            print(f"Processing attachment data: url={url}, type={resource_type}") # DEBUG
            if url and isinstance(url, str):
                try:
                    attachment = Attachment.objects.create(url=url, resource_type=resource_type)
                    new_attachment_ids.append(attachment.id)
                    print(f"DEBUG: Created Attachment ID: {attachment.id}") # DEBUG
                except Exception as e:
                    print(f"ERROR creating attachment for {url}: {e}") # DEBUG
        if new_attachment_ids:
            try:
                print(f"DEBUG: Setting attachments for post {instance.id} with IDs: {new_attachment_ids}") # DEBUG
                instance.attachments.set(new_attachment_ids)
                print("DEBUG: instance.attachments.set() called.") # DEBUG
            except Exception as e:
                print(f"ERROR during instance.attachments.set(): {e}") # DEBUG
        

    @transaction.atomic
    def create(self, validated_data):
        print("\n--- CommentSerializer CREATE ---") # DEBUG
        # --- CORRECTED: Pop 'attachments_input' ---
        attachments_data = validated_data.pop('attachments_input', [])
        print(f"Popped 'attachments_input' for comment: {attachments_data}") # DEBUG
        # --- End Correction ---

        # Author/Post passed from view's perform_create
        comment = Comment.objects.create(**validated_data)
        print(f"Comment instance created with ID: {comment.id}") # DEBUG

        # --- CORRECTED: Call helper for list of dicts ---
        if attachments_data:
            print("Calling _handle_attachments_from_data for comment...") # DEBUG
            self._handle_attachments_from_data(comment, attachments_data)
        else:
            print("No attachments_input data found for comment.") # DEBUG
        # --- End Correction ---
        print("--- CommentSerializer CREATE Finished ---") # DEBUG
        return comment    


class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Display username as string
    post = serializers.StringRelatedField()  # Display post as string (useful for debugging)
    comment = serializers.StringRelatedField()  # Display comment as string (useful for debugging)

    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'post', 'comment', 'timestamp']

class EditCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['comment']
        extra_kwargs = {
            'comment': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'blank': "Comment cannot be empty"
                }
            }
        }

class DeleteCommentSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(
        required=True,
        error_messages={
            'required': 'Please confirm deletion',
            'invalid': 'Confirmation must be a boolean value'
        }
    )


class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    post = serializers.StringRelatedField()
    comment = serializers.StringRelatedField()

    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'post', 'comment', 'timestamp']



class ReplySerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    reaction_counts = serializers.SerializerMethodField()
    attachment_urls = serializers.ListField(
        child=serializers.URLField(max_length=500),
        write_only=True, 
        required=False
    )

    class Meta:
        model = Reply
        fields = [
            'id', 'author', 'body', 'created_on', 
            'reaction_counts', 'attachments', 'attachment_urls'
        ]
        read_only_fields = ['author', 'created_on']

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()

    def validate_body(self, value):
        trimmed = value.strip()
        if len(trimmed) > 1500:
            raise serializers.ValidationError("Reply cannot exceed 1500 characters")
        return trimmed
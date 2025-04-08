# from rest_framework import serializers
# from .models import Post, Comment, Attachment, Reaction, Reply
# from users.models import User # Assuming User is in users app
# from django.db import transaction
# import mimetypes # For checking file types
# from users.serializers import AuthorSerializer
# import pprint # Add this at the top of the file




# class AttachmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Attachment
#         fields = ['id', 'url', 'resource_type'] # Only need URL and type usually
#         read_only_fields = ['id']


# class PostAuthorSerializer(serializers.ModelSerializer):
#     # Get profile picture URL from related Profile model
#     profile_picture = serializers.URLField(source='profile.profile_picture', read_only=True, allow_null=True)
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture']
#         read_only = True


# class PostSerializer(serializers.ModelSerializer):
#     author = PostAuthorSerializer(read_only=True) # Use specific nested serializer
#     attachments = AttachmentSerializer(many=True, read_only=True)
#     reaction_counts = serializers.SerializerMethodField(read_only=True)
#     comments_count = serializers.IntegerField(source='comments.count', read_only=True) # Efficient count

#     # Accept list of Cloudinary URLs on write
#     attachments_input = serializers.ListField(
#         child=serializers.DictField(child=serializers.CharField(max_length=500, allow_blank=True)), 
#         write_only=True, required=False
#     )
    
#     class Meta:
#         model = Post
#         fields = [
#             "id", "author", "body", "created_on",
#             "reaction_counts", "attachments", # Read
#             "attachments_input", "comments_count" # Write
#         ]
#         read_only_fields = ["id", "author", "created_on", "reaction_counts", "attachments", "attachment_input"]
        
    
#     def validate_body(self, value):
#         trimmed = value.strip()
#         if len(trimmed) > 2500:
#             raise serializers.ValidationError("Post cannot exceed 2500 characters")
#         return trimmed

#     def get_reaction_counts(self, obj): # Keep this
#         return obj.reaction_counts() if hasattr(obj, 'reaction_counts') else {}

#     def _handle_attachments_from_data(self, instance, attachments_data):
#         print(f"--- _handle_attachments for post {instance.id} ---") # DEBUG
#         print(f"Received attachments data list: {attachments_data}") # DEBUG
#         if not isinstance(attachments_data, list): print("DEBUG: attachments_data not a list."); return
#         new_attachment_ids = []
#         for attach_data in attachments_data: # Iterate over dictionaries
#             url = attach_data.get('url')
#             resource_type = attach_data.get('resource_type', 'image')[:20] # Get type, limit length
#             print(f"Processing attachment data: url={url}, type={resource_type}") # DEBUG
#             if url and isinstance(url, str):
#                 try:
#                     attachment = Attachment.objects.create(url=url, resource_type=resource_type)
#                     new_attachment_ids.append(attachment.id)
#                     print(f"DEBUG: Created Attachment ID: {attachment.id}") # DEBUG
#                 except Exception as e:
#                     print(f"ERROR creating attachment for {url}: {e}") # DEBUG
#         if new_attachment_ids:
#             try:
#                 print(f"DEBUG: Setting attachments for post {instance.id} with IDs: {new_attachment_ids}") # DEBUG
#                 instance.attachments.set(new_attachment_ids)
#                 print("DEBUG: instance.attachments.set() called.") # DEBUG
#             except Exception as e:
#                 print(f"ERROR during instance.attachments.set(): {e}") # DEBUG
#         else:
#             print("DEBUG: No new attachment instances created/processed.") # DEBUG
#         print(f"--- _handle_attachments finished ---") # DEBUG

#     @transaction.atomic
#     def create(self, validated_data):
#         print("\n--- PostSerializer CREATE ---")
#         print("Validated data received by create:") # Log data received from save()
#         pprint.pprint(validated_data)

#         attachments_data = validated_data.pop('attachments_input', [])
#         print(f"Popped attachments_input: {attachments_data}")

#         # --- CORRECTED CREATE CALL ---
#         # Extract known fields explicitly instead of using **validated_data
#         body = validated_data.get('body')
#         author = validated_data.get('author') # Get author passed from view via save()

#         if not author:
#             # Fallback or raise error if author wasn't passed correctly from view
#             author = self.context['request'].user
#             print("Warning: Author not found in validated_data, using context user.")

#         print(f"Data for Post.objects.create: author={author}, body={body[:50]}...") # Log data
#         post = Post.objects.create(author=author, body=body)
#         # --- END CORRECTION ---

#         print(f"Post instance created with ID: {post.id}")

#         if attachments_data:
#             print("Calling _handle_attachments_from_data...")
#             self._handle_attachments_from_data(post, attachments_data)
#         else:
#             print("No attachments_input data found to process.")

#         print("--- PostSerializer CREATE Finished ---")
#         return post

    
#     @transaction.atomic
#     def update(self, instance, validated_data):
#         attachments_data = validated_data.pop('attachments_input', None)
#         instance = super().update(instance, validated_data) # Update body etc.
#         if attachments_data is not None:
#             instance.attachments.clear() # Consider deleting old Attachment objects too?
#             self._handle_attachments_from_data(instance, attachments_data)
#         return instance


# class CommentSerializer(serializers.ModelSerializer):
#     author = PostAuthorSerializer(read_only=True) # Use same author detail serializer
#     attachments = AttachmentSerializer(many=True, read_only=True)
#     reaction_counts = serializers.SerializerMethodField(read_only=True)
#     post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), write_only=True)

#     attachments_input = serializers.ListField(
#         child=serializers.DictField(child=serializers.CharField(max_length=550, allow_blank=True)),
#         write_only=True, required=False
#     )

#     class Meta:
#         model = Comment
#         fields = [
#             "id", "post", "author", "comment", "created_on", "attachments", # Base + Read
#             "reaction_counts", #"replies_count", # Counts
#             "attachments_input" # Write
#         ]
#         read_only_fields = ["id", "author", "created_on", "attachments", "reaction_counts"] # Removed 'post'


#     def validate_comment(self, value):
#         trimmed = value.strip()
#         if len(trimmed) > 1500:
#             raise serializers.ValidationError("Comment cannot exceed 1500 characters")
#         return trimmed


#     def get_reaction_counts(self, obj): # Keep
#         return obj.reaction_counts() if hasattr(obj, 'reaction_counts') else {}

#     # Add helper or reuse logic
#     def _handle_attachments_from_urls(self, instance, attachments_data):
#         print(f"--- _handle_attachments for post {instance.id} ---") # DEBUG
#         print(f"Received attachments data list: {attachments_data}") # DEBUG
#         if not isinstance(attachments_data, list): print("DEBUG: attachments_data not a list."); return
#         new_attachment_ids = []
#         for attach_data in attachments_data: # Iterate over dictionaries
#             url = attach_data.get('url')
#             resource_type = attach_data.get('resource_type', 'image') # Default to image if not provided
#             print(f"Processing attachment data: url={url}, type={resource_type}") # DEBUG
#             if url and isinstance(url, str):
#                 try:
#                     attachment = Attachment.objects.create(url=url, resource_type=resource_type)
#                     new_attachment_ids.append(attachment.id)
#                     print(f"DEBUG: Created Attachment ID: {attachment.id}") # DEBUG
#                 except Exception as e:
#                     print(f"ERROR creating attachment for {url}: {e}") # DEBUG
#         if new_attachment_ids:
#             try:
#                 print(f"DEBUG: Setting attachments for post {instance.id} with IDs: {new_attachment_ids}") # DEBUG
#                 instance.attachments.set(new_attachment_ids)
#                 print("DEBUG: instance.attachments.set() called.") # DEBUG
#             except Exception as e:
#                 print(f"ERROR during instance.attachments.set(): {e}") # DEBUG
        

#     @transaction.atomic
#     def create(self, validated_data):
#         print("\n--- CommentSerializer CREATE ---") # DEBUG
#         # --- CORRECTED: Pop 'attachments_input' ---
#         attachments_data = validated_data.pop('attachments_input', [])
#         print(f"Popped 'attachments_input' for comment: {attachments_data}") # DEBUG
#         # --- End Correction ---

#         # Author/Post passed from view's perform_create
#         comment = Comment.objects.create(**validated_data)
#         print(f"Comment instance created with ID: {comment.id}") # DEBUG

#         # --- CORRECTED: Call helper for list of dicts ---
#         if attachments_data:
#             print("Calling _handle_attachments_from_data for comment...") # DEBUG
#             self._handle_attachments_from_data(comment, attachments_data)
#         else:
#             print("No attachments_input data found for comment.") # DEBUG
#         # --- End Correction ---
#         print("--- CommentSerializer CREATE Finished ---") # DEBUG
#         return comment    


# class ReactionSerializer(serializers.ModelSerializer):
#     user = PostAuthorSerializer(read_only=True) # Show user details
#     class Meta: model = Reaction; fields = ['id', 'user', 'reaction_type'] # Simplified read


#     class Meta:
#         model = Reaction
#         fields = ['id', 'user', 'reaction_type', 'post', 'comment', 'timestamp']

# class EditCommentSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Comment
#         fields = ['comment']
#         extra_kwargs = {
#             'comment': {
#                 'required': True,
#                 'allow_blank': False,
#                 'error_messages': {
#                     'blank': "Comment cannot be empty"
#                 }
#             }
#         }

# class DeleteCommentSerializer(serializers.Serializer):
#     confirmation = serializers.BooleanField(
#         required=True,
#         error_messages={
#             'required': 'Please confirm deletion',
#             'invalid': 'Confirmation must be a boolean value'
#         }
#     )


# class ReactionSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField()
#     post = serializers.StringRelatedField()
#     comment = serializers.StringRelatedField()

#     class Meta:
#         model = Reaction
#         fields = ['id', 'user', 'reaction_type', 'post', 'comment', 'timestamp']



# class ReplySerializer(serializers.ModelSerializer):
#     author = AuthorSerializer(read_only=True)
#     attachments = AttachmentSerializer(many=True, read_only=True)
#     reaction_counts = serializers.SerializerMethodField()
#     attachment_urls = serializers.ListField(
#         child=serializers.URLField(max_length=500),
#         write_only=True, 
#         required=False
#     )

#     class Meta:
#         model = Reply
#         fields = [
#             'id', 'author', 'body', 'created_on', 
#             'reaction_counts', 'attachments', 'attachment_urls'
#         ]
#         read_only_fields = ['author', 'created_on']

#     def get_reaction_counts(self, obj):
#         return obj.reaction_counts()

#     def validate_body(self, value):
#         trimmed = value.strip()
#         if len(trimmed) > 1500:
#             raise serializers.ValidationError("Reply cannot exceed 1500 characters")
#         return trimmed

# posts/serializers.py
import pprint
from rest_framework import serializers
from django.db import transaction
from .models import Post, Comment, Attachment, Reaction, Reply
from users.models import User
# Use the simplified AuthorSerializer from users app
from users.serializers import AuthorSerializer # Adjust path if needed

# --- Attachment Serializer ---
class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'url', 'resource_type'] # Only need URL and type
        read_only_fields = ['id']

# --- Base Serializer for handling attachments from URLs ---
class BaseAttachmentHandlerSerializer(serializers.ModelSerializer):
    # Common field to accept attachment data [{url, resource_type}, ...] from widget
    attachments_input = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(max_length=550, allow_blank=True)),
        write_only=True, required=False
    )
    # Common field to read existing attachments
    attachments = AttachmentSerializer(many=True, read_only=True)

    def _handle_attachments(self, instance, attachments_data):
        """Helper: Creates Attachment objects from data list and links to instance."""
        if not isinstance(attachments_data, list): return
        new_attachment_ids = []
        print(f"DEBUG [_handle_attachments]: Received data: {attachments_data}")
        for attach_data in attachments_data:
            url = attach_data.get('url')
            resource_type = attach_data.get('resource_type', 'image')[:20] # Limit length
            if url and isinstance(url, str):
                try:
                    attachment = Attachment.objects.create(url=url, resource_type=resource_type)
                    new_attachment_ids.append(attachment.id)
                    print(f"DEBUG [_handle_attachments]: Created Attachment ID: {attachment.id}")
                except Exception as e: print(f"ERROR creating attachment for {url}: {e}")
        if new_attachment_ids:
            try:
                print(f"DEBUG [_handle_attachments]: Setting M2M for instance {instance.id} with IDs: {new_attachment_ids}")
                instance.attachments.set(new_attachment_ids) # Set ManyToMany
            except Exception as e: print(f"ERROR during attachments.set(): {e}")

    # --- Base create/update methods ---
    @transaction.atomic
    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments_input', [])
        instance = super().create(validated_data) # Create main instance (Post/Comment/Reply)
        self._handle_attachments(instance, attachments_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        attachments_data = validated_data.pop('attachments_input', None)
        instance = super().update(instance, validated_data) # Update main fields
        if attachments_data is not None: # Only update attachments if key was provided
            # Clear old & create new (doesn't delete from Cloudinary)
            instance.attachments.all().delete() # Delete old Attachment records
            self._handle_attachments(instance, attachments_data)
        return instance

# --- Post Serializer ---
class PostSerializer(BaseAttachmentHandlerSerializer): # Inherit helper logic
    author = AuthorSerializer(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Post
        fields = [ "id", "author", "body", "created_on", "attachments", "reaction_counts", "comments_count", "attachments_input" ]
        read_only_fields = ["id", "author", "created_on", "attachments", "reaction_counts", "comments_count"]

    def get_reaction_counts(self, obj): return obj.reaction_counts()
    def validate_body(self, value): # Add validation
        trimmed = value.strip();
        if not trimmed : raise serializers.ValidationError("Body cannot be empty.")
        if len(trimmed) > 2500: raise serializers.ValidationError("Max 2500 characters.")
        return trimmed
    @transaction.atomic
    def create(self, validated_data):
        print("\n--- PostSerializer CREATE ---") # DEBUG
        # validated_data here includes 'body' and 'author' (passed from save)
        print("Validated data received by create:") # DEBUG
        pprint.pprint(validated_data) # DEBUG

        # Pop attachments first, if any
        attachments_data = validated_data.pop('attachments_input', [])
        print(f"Popped attachments_input: {attachments_data}") # DEBUG

        # --- CORRECTED Post.objects.create CALL ---
        # Extract the 'author' object passed from view via save()
        # And extract other direct fields ('body' in this case)
        author_instance = validated_data.get('author') # Still contains the User instance
        body_text = validated_data.get('body')


        # Check if author was correctly passed (should be guaranteed by IsAuthenticated + perform_create)
        if not author_instance:
            print("ERROR: Author instance missing in validated_data during create!")
            # You might want to raise an error here or try getting from context as fallback
            raise serializers.ValidationError("Author could not be determined for post creation.")

        print(f"Explicitly Creating Post with author='{author_instance}', body='{body_text[:50]}...'") # DEBUG

        # Create the Post instance by explicitly passing fields
        # DO NOT use **validated_data here as it contains the author object incorrectly
        print(f"Explicitly Creating Post with author_id={author_instance.id}, body={body_text[:50]}...") # Log ID
        try:
            post = Post.objects.create(
                author_id=author_instance.id, # Pass the ID directly
                body=body_text
            )
            print(f"Post instance created with ID: {post.id}") # DEBUG
        except Exception as e:
            print(f"!!! ERROR during Post.objects.create: {e}") # Log direct create error
            # Re-raise to signal DRF about the failure
            raise serializers.ValidationError(f"Database error during post creation: {e}")

        # --- END CORRECTION ---

        # Handle attachments using the created post instance
        if attachments_data:
            print("Calling _handle_attachments_from_data...") # DEBUG
            self._handle_attachments(post, attachments_data)
        else:
            print("No attachments_input data found to process.") # DEBUG

        print("--- PostSerializer CREATE Finished ---") # DEBUG
        return post


# --- Comment Serializer ---
class CommentSerializer(BaseAttachmentHandlerSerializer): # Inherit helper logic
    author = AuthorSerializer(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    # post = serializers.PrimaryKeyRelatedField(read_only=True) # Read post ID
    post_id = serializers.UUIDField(write_only=True) # Accept post UUID on write

    class Meta:
        model = Comment
        fields = [ "id", "post", "author", "comment", "created_on", "attachments", "reaction_counts", "attachments_input", "post_id"]
        read_only_fields = ["id", "post", "author", "created_on", "attachments", "reaction_counts"]

    def validate_comment(self, value): # Add validation
        trimmed = value.strip();
        if not trimmed : raise serializers.ValidationError("Comment cannot be empty.")
        if len(trimmed) > 1500: raise serializers.ValidationError("Max 1500 characters.")
        return trimmed

    def get_reaction_counts(self, obj): return obj.reaction_counts()

    # Override create slightly to handle post association correctly
    @transaction.atomic
    def create(self, validated_data):
        # validated_data already includes 'post_id' from write_only field
        attachments_data = validated_data.pop('attachments_input', [])
        # Author passed from view
        comment = Comment.objects.create(**validated_data)
        self._handle_attachments(comment, attachments_data)
        return comment


# --- Reply Serializer (If needed, with attachment handling) ---
class ReplySerializer(BaseAttachmentHandlerSerializer): # Inherit helper logic
    author = AuthorSerializer(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    # comment = serializers.PrimaryKeyRelatedField(read_only=True) # Read comment ID
    comment_id = serializers.UUIDField(write_only=True) # Accept comment UUID on write

    class Meta:
        model = Reply
        fields = [ 'id', 'author', 'comment', 'parent_reply', 'body', 'created_on', 'attachments', 'reaction_counts', 'attachments_input', 'comment_id' ]
        read_only_fields = ['id', 'author', 'created_on', 'attachments', 'reaction_counts', 'comment', 'parent_reply']

    def validate_body(self, value): # Add validation
        trimmed = value.strip();
        if not trimmed : raise serializers.ValidationError("Reply cannot be empty.")
        if len(trimmed) > 1500: raise serializers.ValidationError("Max 1500 characters.")
        return trimmed

    def get_reaction_counts(self, obj): return obj.reaction_counts() if hasattr(obj, 'reaction_counts') else {}

    @transaction.atomic
    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments_input', [])
        # Author/Comment passed from view
        reply = Reply.objects.create(**validated_data)
        self._handle_attachments(reply, attachments_data)
        return reply

# --- Other Serializers (Reaction, EditComment, DeleteComment) ---
class ReactionSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True) # Use consistent author representation
    class Meta: model = Reaction; fields = ['id', 'user', 'reaction_type'] # Simple read output

class EditCommentSerializer(serializers.ModelSerializer): # For PUT/PATCH on comments
    class Meta: model = Comment; fields = ['comment']; # Keep simple body update

class DeleteCommentSerializer(serializers.Serializer): # For DELETE confirmation body
    confirmation = serializers.BooleanField(required=True)
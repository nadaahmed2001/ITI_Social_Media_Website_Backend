from rest_framework import serializers
from .models import Post, Comment, Attachment, Reaction
from users.models import Profile

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'image', 'video', 'uploaded_on']

class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    author_profile_picture = serializers.SerializerMethodField()
    reaction_counts = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    attachment_urls = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Post
        fields = ["id", "author", "author_profile_picture", "body", "created_on", 
                "reaction_counts", "attachments", "attachment_urls"]

    def get_author(self, obj):
        return obj.author.username

    def get_author_profile_picture(self, obj):
        profile = Profile.objects.filter(user=obj.author).first()
        return profile.profile_picture if profile else None

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()

    def create(self, validated_data):
        attachment_urls = validated_data.pop('attachment_urls', [])
        post = Post.objects.create(**validated_data)
        
        for url in attachment_urls:
            is_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
            is_video = any(ext in url.lower() for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv'])
            
            attachment = Attachment.objects.create(
                image=url if is_image else None,
                video=url if is_video else None
            )
            post.attachments.add(attachment)
        
        return post



class CommentSerializer(serializers.ModelSerializer):
    # Keep read-only fields for displaying author info
    author = serializers.SerializerMethodField(read_only=True) 
    author_profile_picture = serializers.SerializerMethodField(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    # Keep read-only field for displaying attachments in responses
    attachments = AttachmentSerializer(many=True, read_only=True) 

    # --- Add write-only field to ACCEPT the URL from the frontend ---
    attachment_url = serializers.URLField(write_only=True, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Comment
        # Add 'attachment_url' to the list of fields the serializer handles
        fields = ["id", "post", "author", "author_profile_picture", "comment", 
                "created_on", "reaction_counts", "attachments", "attachment_url"]
        # Define fields that shouldn't be editable directly via the main serializer input
        read_only_fields = ["author", "author_profile_picture", "reaction_counts", "attachments", "created_on"] 

    def get_author(self, obj):
        return obj.author.username

    def get_author_profile_picture(self, obj):
        # Optimization: Use select_related('author__profile') in the view's queryset
        profile = getattr(obj.author, 'profile', None) 
        # return profile.profile_picture if profile else None
        # Or keep your try/except block if profile isn't always related via 'profile'
        try:
            profile = Profile.objects.get(user=obj.author)
            return profile.profile_picture
        except Profile.DoesNotExist:
            return None

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()

    # --- Modified create method to handle attachment_url ---
    def create(self, validated_data):
        # Pop the attachment_url if it was sent and validated
        attachment_url = validated_data.pop('attachment_url', None)
        
        # Get the author from the request context (set by IsAuthenticated)
        # validated_data['author'] = self.context['request'].user # This should happen automatically if author is not read_only? 
        # Let's assume author is set correctly by view/DRF.

        # Create the comment instance without the attachment_url
        comment = Comment.objects.create(**validated_data)
        
        # If an attachment URL was provided, create the Attachment object
        if attachment_url:
            print(f"Attempting to create attachment for comment {comment.id} from URL: {attachment_url}") # Debug log
            try:
                # Simple check for image/video based on common extensions in the URL
                # You might need a more robust check depending on your Cloudinary setup
                is_image = any(ext in attachment_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
                is_video = any(ext in attachment_url.lower() for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv'])
                
                # Create Attachment object using the URL fields in your model
                attachment = Attachment.objects.create(
                    image=attachment_url if is_image else None,
                    video=attachment_url if is_video else None 
                    # Add other fields if your Attachment model has them (e.g., resource_type)
                )
                # Add the created attachment to the comment's ManyToMany field
                comment.attachments.add(attachment)
                print(f"Successfully created and linked attachment {attachment.id}") # Debug log
            except Exception as e:
                # Log if attachment creation fails, but maybe let comment creation succeed
                print(f"ERROR creating/linking attachment from URL {attachment_url} for comment {comment.id}: {e}")
                # Consider if you should delete the comment here if attachment is mandatory, 
                # or if comment without attachment is acceptable.

        return comment

    
class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Display username as string
    post = serializers.StringRelatedField()  # Display post as string (useful for debugging)
    comment = serializers.StringRelatedField()  # Display comment as string (useful for debugging)

    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'post', 'comment', 'timestamp']
## 
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
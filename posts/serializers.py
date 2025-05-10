from rest_framework import serializers
from .models import Post,SavedPost, Comment, Attachment, Reaction
from users.models import Profile, User
import re

# posts/serializers.py
from rest_framework import serializers
from .models import Reaction # Keep other necessary model imports
from users.models import User, Profile # Import User and Profile


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
    author_id = serializers.SerializerMethodField(read_only=True)
    is_saved = serializers.SerializerMethodField()
    # mentions = serializers.SlugRelatedField(
    #     queryset=User.objects.all(), 
    #     slug_field='username', 
    #     many=True, 
    #     required=False, 
    #     allow_empty=True  
    # )


    class Meta:
        model = Post
        fields = ["id", "author", "author_id", "author_profile_picture", "body", 
                "created_on", "reaction_counts", "attachments", "attachment_urls", "is_saved", ]

    def get_author(self, obj):
        return obj.author.username
    
    def get_author_id(self, obj):
        # Assumes Profile.id is the UUID associated with the User
        # Use select_related('author__profile') in the view's queryset
        profile = getattr(obj.author, 'profile', None)
        # Return as string to match frontend context UUID string
        return str(profile.id) if profile and hasattr(profile, 'id') else None

    def get_author_profile_picture(self, obj):
        profile = Profile.objects.filter(user=obj.author).first()
        return profile.profile_picture if profile else None

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()

    def get_is_saved(self, obj):
        """
        Check if the requesting user has saved this post.
        """
        user = self.context['request'].user
        if user and user.is_authenticated:
            # Check if a SavedPost record exists for this user and post
            return SavedPost.objects.filter(user=user, post=obj).exists()
        return False # Not saved if user is not authenticated
    
    # def extract_mentions(self, text):
    #     mentioned_usernames = set(re.findall(r'@(\w+)', text))
    #     mentioned_users = User.objects.filter(username__in=mentioned_usernames)
    #     return mentioned_users


    def create(self, validated_data):
        attachment_urls = validated_data.pop('attachment_urls', [])
        # body = validated_data.get('body', '')
        post = Post.objects.create(**validated_data)
        
        # Handle mentions
        # mentions = self.extract_mentions(body)
        # post.mentions.set(mentions)

        for url in attachment_urls:
            is_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
            is_video = any(ext in url.lower() for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv'])
            
            attachment = Attachment.objects.create(
                image=url if is_image else None,
                video=url if is_video else None
            )
            post.attachments.add(attachment)
        
        return post


class SavedPostSerializer(serializers.ModelSerializer):
    # You might want to nest the PostSerializer here
    post = PostSerializer(read_only=True)
    class Meta:
        model = SavedPost
        fields = ['id', 'post', 'saved_on']
        

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(read_only=True)
    author_profile_picture = serializers.SerializerMethodField(read_only=True)
    reaction_counts = serializers.SerializerMethodField(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    attachment_url = serializers.URLField(write_only=True, required=False, allow_null=True, allow_blank=True)
    author_id = serializers.SerializerMethodField(read_only=True)
    my_reaction = serializers.SerializerMethodField(read_only=True) # <-- ADD THIS
    # mentions = serializers.SlugRelatedField(
    #         queryset=User.objects.all(), 
    #         slug_field='username', 
    #         many=True, 
    #         required=False, 
    #         allow_empty=True  
    #     )

    class Meta:
        model = Comment
        # Keep 'author_id' in fields
        fields = ["id", "post", "author", "author_id", "author_profile_picture", "comment",
                "created_on", "reaction_counts", "my_reaction", "attachments", "attachment_url", ]
        # read_only_fields are implicitly handled for method fields, but keep others
        read_only_fields = ["author", "author_profile_picture", "reaction_counts", "attachments", "created_on"]


    def get_author(self, obj):
        return obj.author.username
    
    def get_author_id(self, obj):
        # obj is a Comment instance
        # Assumes the UUID identifier used by your frontend/account API 
        # is the primary key of the related Profile model.
        # Use select_related('author__profile') in the view's queryset for efficiency.
        profile = getattr(obj.author, 'profile', None) 
        if profile and hasattr(profile, 'id'):
            # Return the Profile's ID (assumed to be the UUID) AS A STRING
            return str(profile.id) 
        # Fallback or error handling if profile or profile.id doesn't exist
        return None 
    

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

    def get_my_reaction(self, obj):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            return None
        try:
            reaction = Reaction.objects.get(comment=obj, user=user)
            return reaction.reaction_type
        except Reaction.DoesNotExist:
            return None

    # def extract_mentions(self, text):
    #     mentioned_usernames = set(re.findall(r'@(\w+)', text))
    #     mentioned_users = User.objects.filter(username__in=mentioned_usernames)
    #     return mentioned_users
            
    # --- Modified create method to handle attachment_url ---
    def create(self, validated_data):
        # Pop the attachment_url if it was sent and validated
        attachment_url = validated_data.pop('attachment_url', None)
        # body = validated_data.get('comment', '')
        
        # Get the author from the request context (set by IsAuthenticated)
        # validated_data['author'] = self.context['request'].user # This should happen automatically if author is not read_only? 
        # Let's assume author is set correctly by view/DRF.

        # Create the comment instance without the attachment_url
        comment = Comment.objects.create(**validated_data)
        
        # # Handle mentions
        # mentions = self.extract_mentions(body)
        # comment.mentions.set(mentions)
        
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

    
class UserInReactionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True) # Use UUIDField
    username = serializers.CharField(read_only=True)
    
    class Meta:
        model = User 
        fields = ['id', 'username']

# Remove or comment out UserInReactionSerializer if not used elsewhere
# class UserInReactionSerializer(serializers.ModelSerializer): ...

class ReactionSerializer(serializers.ModelSerializer): 
    # Get username directly from the related user model
    user_username = serializers.CharField(source='user.username', read_only=True) 
    # Use a method field to explicitly get the Profile's UUID as user_id
    user_id = serializers.SerializerMethodField(read_only=True) 
    user_profile_picture = serializers.SerializerMethodField(read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True) 
    comment = serializers.PrimaryKeyRelatedField(read_only=True) 

    class Meta: 
        model = Reaction
        # Use user_id and user_username instead of the nested user object
        fields = [
            'id', 
            'user_id',          # Profile UUID (from get_user_id)
            'user_username',    # User's username
            'user_profile_picture', # Profile picture URL (from get_user_profile_picture)
            'reaction_type', 
            'post', 
            'comment', 
            'timestamp'
        ]
    
    # This method provides the value for the 'user_id' field defined above
    def get_user_id(self, obj):
        # obj is a Reaction instance. obj.user is the User instance.
        try:
            # Access the related profile's id (which IS the UUID)
            # This relies on using select_related('user__profile') in the ViewSet/View
            profile_uuid = obj.user.profile.id 
            # Return the UUID AS A STRING to match frontend context
            return str(profile_uuid) 
        except Profile.DoesNotExist:
            # Handle case where profile might not exist for some reason
            print(f"Warning: Profile not found for user {obj.user.id} in ReactionSerializer")
            return None
        except AttributeError:
            # Handle case where select_related might not have been used efficiently
            print(f"Warning: 'profile' attribute not readily available for user {obj.user.id}. Querying separately.")
            try:
                profile = Profile.objects.get(user=obj.user)
                return str(profile.id)
            except Profile.DoesNotExist:
                print(f"Error: Profile truly does not exist for user {obj.user.id}")
                return None
        except Exception as e:
                print(f"Error getting profile ID for reaction {obj.id}: {e}")
                return None
    
    def get_user_profile_picture(self, obj):
        # obj is a Reaction instance
        # Requires select_related('user__profile') in view
        profile = getattr(obj.user, 'profile', None)
        # Return profile_picture URL if profile exists and has the attribute
        return profile.profile_picture if profile and hasattr(profile, 'profile_picture') else None

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
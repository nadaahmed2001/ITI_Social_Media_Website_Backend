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
            is_image = any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif'])
            is_video = any(ext in url.lower() for ext in ['.mp4', '.mov'])
            
            attachment = Attachment.objects.create(
                image=url if is_image else None,
                video=url if is_video else None
            )
            post.attachments.add(attachment)
        
        return post




class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    author_profile_picture = serializers.SerializerMethodField()
    reaction_counts = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, required=False)

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "author_profile_picture", "comment", "created_on", "reaction_counts", "attachments"]

    def get_author(self, obj):
        return obj.author.username

    def get_author_profile_picture(self, obj):
        try:
            profile = Profile.objects.get(user=obj.author)
            return profile.profile_picture
        except Profile.DoesNotExist:
            return None

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()

    def create(self, validated_data):
        attachments_data = self.context['request'].FILES.getlist('attachments')
        comment = Comment.objects.create(**validated_data)
        
        for attachment_data in attachments_data:
            attachment = Attachment.objects.create(image=attachment_data)
            comment.attachments.add(attachment)
        
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
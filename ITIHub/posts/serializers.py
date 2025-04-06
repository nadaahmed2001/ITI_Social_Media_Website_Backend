from rest_framework import serializers
from .models import Post, Comment, Attachment, Reaction

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    reaction_counts = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ["id", "author", "body", "created_on", "reaction_counts", "attachments"]

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()

    def create(self, validated_data):
        attachments_data = self.context['request'].FILES.getlist('attachments')
        post = Post.objects.create(**validated_data)
        
        for attachment_data in attachments_data:
            attachment = Attachment.objects.create(image=attachment_data)
            post.attachments.add(attachment)
        
        return post

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    reaction_counts = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, required=False)

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "comment", "created_on", "reaction_counts", "attachments"]

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

# from rest_framework import serializers
# from .models import Post, Comment, Attachment, Reaction

# class AttachmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Attachment
#         fields = '__all__'

# class PostSerializer(serializers.ModelSerializer):
#     author = serializers.StringRelatedField()
#     reaction_counts = serializers.SerializerMethodField()
#     attachments = AttachmentSerializer(many=True, required=False)

#     class Meta:
#         model = Post
#         fields = ["id", "author", "body", "created_on", "reaction_counts", "attachments"]

#     def get_reaction_counts(self, obj):
#         return obj.reaction_counts()

#     def create(self, validated_data):
#         attachments_data = self.context['request'].FILES.getlist('attachments')
#         post = Post.objects.create(**validated_data)
        
#         for attachment_data in attachments_data:
#             attachment = Attachment.objects.create(image=attachment_data)
#             post.attachments.add(attachment)
        
#         return post

# class CommentSerializer(serializers.ModelSerializer):
#     author = serializers.StringRelatedField()
#     reaction_counts = serializers.SerializerMethodField()
#     attachments = AttachmentSerializer(many=True, required=False)

#     class Meta:
#         model = Comment
#         fields = ["id", "post", "author", "comment", "created_on", "reaction_counts", "attachments"]

#     def get_reaction_counts(self, obj):
#         return obj.reaction_counts()

#     def create(self, validated_data):
#         attachments_data = self.context['request'].FILES.getlist('attachments')
#         comment = Comment.objects.create(**validated_data)
        
#         for attachment_data in attachments_data:
#             attachment = Attachment.objects.create(image=attachment_data)
#             comment.attachments.add(attachment)
        
#         return comment

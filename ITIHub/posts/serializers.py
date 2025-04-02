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

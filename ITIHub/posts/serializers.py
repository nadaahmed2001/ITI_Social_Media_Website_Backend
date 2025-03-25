from rest_framework import serializers
from .models import Post, Comment, Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    likes_count = serializers.IntegerField(source="likes.count", read_only=True)
    dislikes_count = serializers.IntegerField(source="dislikes.count", read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "author", "body", "created_on", "likes_count", "dislikes_count", "attachments"]

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "comment", "created_on"]

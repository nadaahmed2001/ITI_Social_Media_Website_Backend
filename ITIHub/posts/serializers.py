from rest_framework import serializers
from .models import Post, Comment, Attachment, Reaction

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    reaction_counts = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "author", "body", "created_on", "reaction_counts", "attachments"]

    def get_reaction_counts(self, obj):
        return {
            reaction: obj.reaction_set.filter(reaction_type=reaction).count()
            for reaction, _ in Reaction.REACTIONS
        }

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    reaction_counts = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "comment", "created_on", "reaction_counts"]

    def get_reaction_counts(self, obj):
        return {
            reaction: obj.reaction_set.filter(reaction_type=reaction).count()
            for reaction, _ in Reaction.REACTIONS
        }

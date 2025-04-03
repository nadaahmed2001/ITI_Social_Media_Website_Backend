from rest_framework import serializers
from .models import GroupChat, GroupMessage, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupChatSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    supervisors = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = GroupChat
        fields = '__all__'

class GroupMessageSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()  # Include the ID field
    sender = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = GroupMessage
        fields = ['id', 'content', 'timestamp', 'sender']  # Include 'id' in the fields

class ChatMessageSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    sender = serializers.ReadOnlyField(source='sender.username')
    receiver = serializers.ReadOnlyField(source='receiver.username')

    class Meta:
        model = ChatMessage
        fields = ['id', 'message', 'timestamp', 'sender', 'receiver']
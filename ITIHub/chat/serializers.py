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
    sender = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = GroupMessage
        fields = ['content', 'timestamp', 'sender']  # Include 'sender' field

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.username')
    receiver = serializers.ReadOnlyField(source='receiver.username')

    class Meta:
        model = ChatMessage
        fields = ['message', 'timestamp', 'sender', 'receiver']  # Include 'sender' and 'receiver' fields
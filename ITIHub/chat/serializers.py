from rest_framework import serializers
from .models import GroupChat, GroupMessage, ChatMessage, ChatBotMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupChatSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    supervisors = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = GroupChat
        fields = ['id', 'name', 'members', 'supervisors', 'last_message']

    def get_last_message(self, obj):
        last_message = GroupMessage.objects.filter(group=obj).order_by('-timestamp').first()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'sender': last_message.sender.username,
                'sender_id': last_message.sender.id,
                'timestamp': last_message.timestamp
            }
        return None

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

class ChatBotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatBotMessage
        fields = ['id', 'user', 'message', 'response', 'timestamp']
        read_only_fields = ['id', 'timestamp']
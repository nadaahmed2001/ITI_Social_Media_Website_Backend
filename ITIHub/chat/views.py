from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
User = get_user_model()

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import GroupChat, GroupMessage, ChatMessage
from .serializers import GroupChatSerializer, GroupMessageSerializer, ChatMessageSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# 🟢 View Group Chat Page
def group_chat_view(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    is_admin = group.supervisors.filter(id=request.user.id).exists()
    
    return render(request, 'chat/group_chat.html', {
        'group': group,
        'is_admin': is_admin
    })

# 🟢 User Chat Dashboard (Lists Group & Private Chats)
class UserChatDashboardView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return {
            "group_chats": GroupChat.objects.filter(members=user),
            "private_chats": ChatMessage.objects.filter(Q(sender=user) | Q(receiver=user)).distinct()
        }

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return Response({
            "groups": GroupChatSerializer(queryset["group_chats"], many=True).data,
            "private_chats": ChatMessageSerializer(queryset["private_chats"], many=True).data
        })

# 🟢 Create/Retrieve Group Chats
class GroupChatListCreateView(generics.ListCreateAPIView):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

# 🟢 Send/Retrieve Group Messages
class GroupMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GroupMessage.objects.filter(group_id=self.kwargs['group_id'])

    def perform_create(self, serializer):
        group = get_object_or_404(GroupChat, id=self.kwargs['group_id'])
        serializer.save(sender=self.request.user, group=group)

# 🟢 Send/Retrieve Private Messages
class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user1 = self.request.user
        user2 = get_object_or_404(User, id=self.kwargs['receiver_id'])
        return ChatMessage.objects.filter(Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1))

    def perform_create(self, serializer):
        receiver = get_object_or_404(User, id=self.kwargs['receiver_id'])
        serializer.save(sender=self.request.user, receiver=receiver)

class PrivateChatUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all users who have private chats with the authenticated user
        chat_users = User.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).distinct()

        # Serialize the user data
        user_data = [{"id": chat_user.id, "username": chat_user.username , "email": chat_user.email} for chat_user in chat_users]
        return Response(user_data)

# 🟢 Clear Group Chat Messages
class ClearGroupChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(GroupChat, id=group_id, members=request.user)
        if not group.supervisors.filter(id=request.user.id).exists():
            return Response({"error": "You do not have permission to clear this group chat."}, status=status.HTTP_403_FORBIDDEN)
        
        GroupMessage.objects.filter(group=group).delete()
        return Response({"message": "Group chat cleared successfully."}, status=status.HTTP_204_NO_CONTENT)

# 🟢 Clear Private Chat Messages
class ClearPrivateChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, receiver_id, *args, **kwargs):
        user1 = request.user
        user2 = get_object_or_404(User, id=receiver_id)
        ChatMessage.objects.filter(Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)).delete()
        return Response({"message": "Private chat cleared successfully."}, status=status.HTTP_204_NO_CONTENT)

# 🟢 Edit a Message
class EditMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, message_id, *args, **kwargs):
        message = get_object_or_404(ChatMessage, id=message_id, sender=request.user)
        new_content = request.data.get("content", "").strip()

        if not new_content:
            return Response({"error": "Message content cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        message.content = new_content
        message.save()
        return Response({"message": "Message updated successfully.", "updated_message": message.content}, status=status.HTTP_200_OK)
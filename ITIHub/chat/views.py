from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Ensure this import is present
from .models import GroupChat, GroupMessage, ChatMessage
from rest_framework import generics, permissions
from .serializers import GroupChatSerializer, GroupMessageSerializer, ChatMessageSerializer

def group_chat_view(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    is_admin = group.supervisors.filter(id=request.user.id).exists()
    
    return render(request, 'chat/group_chat.html', {
        'group': group,
        'is_admin': is_admin
    })

class GroupChatListCreateView(generics.ListCreateAPIView):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class GroupChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupMessageListCreateView(generics.ListCreateAPIView):
    queryset = GroupMessage.objects.all()
    serializer_class = GroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GroupMessage.objects.filter(group_id=self.kwargs['group_id'])

    def perform_create(self, serializer):
        group = get_object_or_404(GroupChat, id=self.kwargs['group_id'])
        serializer.save(sender=self.request.user, group=group)

class ChatMessageListCreateView(generics.ListCreateAPIView):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if 'group_chat' in self.kwargs:
            return ChatMessage.objects.filter(group_chat_id=self.kwargs['group_chat'])
        return ChatMessage.objects.filter(sender=self.request.user, receiver_id=self.kwargs['receiver_id'])

    def perform_create(self, serializer):
        if 'group_chat' in self.kwargs:
            group_chat = get_object_or_404(GroupChat, id=self.kwargs['group_chat'])
            serializer.save(sender=self.request.user, group_chat=group_chat)
        else:
            receiver = get_object_or_404(User, id=self.kwargs['receiver_id'])
            serializer.save(sender=self.request.user, receiver=receiver)

class UserChatListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user1 = self.request.user
        user2 = get_object_or_404(User, id=self.kwargs['user_id'])
        return ChatMessage.objects.filter(
            Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)
        ).order_by('timestamp')
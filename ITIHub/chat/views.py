from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import GroupChat, GroupMessage, ChatMessage, ChatBotMessage
from .serializers import GroupChatSerializer, GroupMessageSerializer, ChatMessageSerializer, ChatBotMessageSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
import openai
import os
from django.conf import settings


# 🟢 View Group Chat Page
@method_decorator(csrf_exempt, name="dispatch")
def group_chat_view(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    is_admin = group.supervisors.filter(id=request.user.id).exists()
    
    return render(request, 'chat/group_chat.html', {
        'group': group,
        'is_admin': is_admin
    })

# 🟢 User Chat Dashboard (Lists Group & Private Chats)
@method_decorator(csrf_exempt, name="dispatch")
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
@method_decorator(csrf_exempt, name="dispatch")
class GroupChatListCreateView(generics.ListCreateAPIView):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

@method_decorator(csrf_exempt, name="dispatch")
class GroupChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

# 🟢 Send/Retrieve Group Messages
@method_decorator(csrf_exempt, name="dispatch")
class GroupMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GroupMessage.objects.filter(group_id=self.kwargs['group_id'])

    def perform_create(self, serializer):
        group = get_object_or_404(GroupChat, id=self.kwargs['group_id'])
        serializer.save(sender=self.request.user, group=group)

# 🟢 Send/Retrieve Private Messages
@method_decorator(csrf_exempt, name="dispatch")
class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user1 = self.request.user
        user2 = get_object_or_404(User, id=self.kwargs['receiver_id'])
        return ChatMessage.objects.filter(Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1))

    def perform_create(self, serializer):
        receiver = get_object_or_404(User, id=self.kwargs['receiver_id'])
        message = serializer.save(sender=self.request.user, receiver=receiver)
        print(f"Message created: {message}")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data['id'] = self.get_queryset().last().id
        return response

@method_decorator(csrf_exempt, name="dispatch")
class PrivateChatUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        # Get all users who have private chats with the authenticated user
        chat_users = User.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).distinct()

        # Prepare the enhanced user data with last messages
        enhanced_user_data = []
        
        for chat_user in chat_users:
            # Get the last message between current user and chat_user
            last_message = ChatMessage.objects.filter(
                Q(sender=user, receiver=chat_user) | Q(sender=chat_user, receiver=user)
            ).order_by('-timestamp').first()
            
            # Create user data object with last message
            user_data = {
                "id": chat_user.id, 
                "username": chat_user.username, 
                "email": chat_user.email
            }
            
            if last_message:
                user_data["last_message"] = {
                    "id": last_message.id,
                    "content": last_message.message,
                    "sender_id": last_message.sender.id,
                    "sender_username": last_message.sender.username,
                    "timestamp": last_message.timestamp
                }
            else:
                user_data["last_message"] = None
                
            enhanced_user_data.append(user_data)
            
        return Response(enhanced_user_data)

# 🟢 Clear Group Chat Messages
@method_decorator(csrf_exempt, name="dispatch")
class ClearGroupChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(GroupChat, id=group_id, members=request.user)
        if not group.supervisors.filter(id=request.user.id).exists():
            return Response({"error": "You do not have permission to clear this group chat."}, status=status.HTTP_403_FORBIDDEN)
        
        GroupMessage.objects.filter(group=group).delete()
        return Response({"message": "Group chat cleared successfully."}, status=status.HTTP_204_NO_CONTENT)

# 🟢 Clear Private Chat Messages
@method_decorator(csrf_exempt, name="dispatch")
class ClearPrivateChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, receiver_id, *args, **kwargs):
        user1 = request.user
        user2 = get_object_or_404(User, id=receiver_id)
        ChatMessage.objects.filter(Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)).delete()
        return Response({"message": "Private chat cleared successfully."}, status=status.HTTP_204_NO_CONTENT)

# 🟢 Edit a Message
@method_decorator(csrf_exempt, name="dispatch")
class EditMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, message_id, *args, **kwargs):
        # Get the message and ensure the sender is the authenticated user
        message = get_object_or_404(ChatMessage, id=message_id)

        # Check if the authenticated user is the sender
        if message.sender != request.user:
            return Response(
                {"error": "You are not authorized to edit this message."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the new content from the request
        new_content = request.data.get("content", "").strip()

        # Validate the new content
        if not new_content:
            return Response(
                {"error": "Message content cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the message content and save it to the database
        message.message = new_content
        message.save()

        # Return a success response
        return Response(
            {"message": "Message updated successfully.", "updated_message": message.message},
            status=status.HTTP_200_OK
        )

@method_decorator(csrf_exempt, name="dispatch")
class EditGroupMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, group_id, message_id, *args, **kwargs):
        # Get the group and ensure the user is a member
        group = get_object_or_404(GroupChat, id=group_id, members=request.user)

        # Get the message and ensure it belongs to the group
        message = get_object_or_404(GroupMessage, id=message_id, group=group)

        # Check if the authenticated user is the sender
        if message.sender != request.user:
            return Response(
                {"error": "You are not authorized to edit this message."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the new content from the request
        new_content = request.data.get("content", "").strip()

        # Validate the new content
        if not new_content:
            return Response(
                {"error": "Message content cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the message content and save it to the database
        message.content = new_content
        message.save()

        # Return a success response
        return Response(
            {"message": "Group message updated successfully.", "updated_message": message.content},
            status=status.HTTP_200_OK
        )

@method_decorator(csrf_exempt, name="dispatch")
class DeleteMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, message_id, *args, **kwargs):
        # Get the message and ensure the sender is the authenticated user
        message = get_object_or_404(ChatMessage, id=message_id, sender=request.user)

        # Delete the message
        message.delete()
        return Response({"message": "Message deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
@api_view(['DELETE'])
def delete_group_message(request, group_id, message_id):
    try:
        # Ensure the user is a member of the group
        group = get_object_or_404(GroupChat, id=group_id, members=request.user)

        # Get the message and ensure it belongs to the group
        message = get_object_or_404(GroupMessage, id=message_id, group=group)

        # Delete the message
        message.delete()
        return Response({"message": "Message deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    except GroupChat.DoesNotExist:
        return Response({"error": "Group not found or you are not a member."}, status=status.HTTP_404_NOT_FOUND)
    except GroupMessage.DoesNotExist:
        return Response({"error": "Message not found in this group."}, status=status.HTTP_404_NOT_FOUND)

@method_decorator(csrf_exempt, name="dispatch")
class ChatBotView(APIView):
    # Add multiple authentication classes to support both token and JWT
    authentication_classes = [JWTAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            # Get message from request
            message = request.data.get('message')
            if not message:
                return Response(
                    {"error": "Please provide a message"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Configure OpenAI client
            openai.api_key = settings.OPENAI_API_KEY
            
            # Print API key for debugging (first few chars)
            api_key = settings.OPENAI_API_KEY
            if api_key:
                masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
                print(f"Using OpenAI API key: {masked_key}")
            else:
                print("WARNING: OpenAI API key is not set!")
            
            # Make API call to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for ITI students."},
                    {"role": "user", "content": message}
                ]
            )
            
            # Extract and return the response
            ai_response = response.choices[0].message.content
            return Response({"response": ai_response}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"ChatBot Error: {str(e)}")
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name="dispatch")
class ChatBotMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        messages = ChatBotMessage.objects.filter(user=user).order_by('timestamp')
        serializer = ChatBotMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
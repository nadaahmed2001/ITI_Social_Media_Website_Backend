import logging  # Add this import
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
from datetime import datetime
from .models import GroupMessage, ChatMessage
from django.contrib.auth.models import User
import os
import django

logger = logging.getLogger(__name__)

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')
django.setup()

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs'].get('group_id')
        self.user = self.scope['user']

        # Ensure the user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return

        # Set the room group name
        self.group_name = f"group_{self.group_id}"

        # Add the user to the WebSocket group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        # Notify the group of a new connection (optional)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_joined",
                "username": self.user.username,
                "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        # Notify the group of a disconnection (optional)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_left",
                "username": self.user.username,
                "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')  # New: Determine the action (send, edit, delete)

        if action == 'send':
            message = data['message']
            # Save the message to the database
            await self.save_group_message(message)
            # Broadcast the message to the group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": self.user.username,
                    "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                }
            )
        elif action == 'edit':
            message_id = data['message_id']
            new_content = data['new_content']
            # Update the message in the database
            await self.edit_group_message(message_id, new_content)
            # Notify the group of the edited message
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "edit_message",
                    "message_id": message_id,
                    "new_content": new_content,
                }
            )
        elif action == 'delete':
            message_id = data['message_id']
            # Delete the message from the database
            await self.delete_group_message(message_id)
            # Notify the group of the deleted message
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "delete_message",
                    "message_id": message_id,
                }
            )

    async def chat_message(self, event):
        # Send the message to WebSocket clients
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event["timestamp"],
        }))

    async def user_joined(self, event):
        # Notify clients of a new user joining
        await self.send(text_data=json.dumps({
            "event": "user_joined",
            "username": event["username"],
            "timestamp": event["timestamp"],
        }))

    async def user_left(self, event):
        # Notify clients of a user leaving
        await self.send(text_data=json.dumps({
            "event": "user_left",
            "username": event["username"],
            "timestamp": event["timestamp"],
        }))

    async def edit_message(self, event):
        # Notify clients of the edited message
        await self.send(text_data=json.dumps({
            "event": "edit_message",
            "message_id": event["message_id"],
            "new_content": event["new_content"],
        }))

    async def delete_message(self, event):
        # Notify clients of the deleted message
        await self.send(text_data=json.dumps({
            "event": "delete_message",
            "message_id": event["message_id"],
        }))

    @sync_to_async
    def save_group_message(self, message):
        # Save the message to the database
        GroupMessage.objects.create(
            group_id=self.group_id,
            sender=self.user,
            content=message
        )

    @sync_to_async
    def edit_group_message(self, message_id, new_content):
        # Update the message in the database
        message = GroupMessage.objects.get(id=message_id, group_id=self.group_id)
        message.content = new_content
        message.save()

    @sync_to_async
    def delete_group_message(self, message_id):
        # Delete the message from the database
        GroupMessage.objects.filter(id=message_id, group_id=self.group_id).delete()

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']

        # Ensure the user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return

        # Create a unique room name for the private chat
        self.group_name = f'private_chat_{min(self.user.id, self.other_user_id)}_{max(self.user.id, self.other_user_id)}'

        # Add the user to the WebSocket group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')  # New: Determine the action (send, edit, delete)

        if action == 'send':
            message = data['message']
            # Save the message to the database
            await self.save_private_message(message)
            # Broadcast the message to the other user
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': self.user.username,
                    'timestamp': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
            )
        elif action == 'edit':
            message_id = data['message_id']
            new_content = data['new_content']
            # Update the message in the database
            await self.edit_private_message(message_id, new_content)
            # Notify the other user of the edited message
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "edit_message",
                    "message_id": message_id,
                    "new_content": new_content,
                }
            )
        elif action == 'delete':
            message_id = data['message_id']
            # Delete the message from the database
            await self.delete_private_message(message_id)
            # Notify the other user of the deleted message
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "delete_message",
                    "message_id": message_id,
                }
            )

    async def chat_message(self, event):
        # Ensure the message is broadcast to all clients in the private chat
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))

    async def edit_message(self, event):
        # Notify clients of the edited message
        await self.send(text_data=json.dumps({
            "event": "edit_message",
            "message_id": event["message_id"],
            "new_content": event["new_content"],
        }))

    async def delete_message(self, event):
        # Notify clients of the deleted message
        await self.send(text_data=json.dumps({
            "event": "delete_message",
            "message_id": event["message_id"],
        }))

    @sync_to_async
    def save_private_message(self, message):
        # Save the message to the database
        other_user = User.objects.get(id=self.other_user_id)
        ChatMessage.objects.create(
            sender=self.user,
            receiver=other_user,
            message=message
        )

    @sync_to_async
    def edit_private_message(self, message_id, new_content):
        # Update the message in the database
        message = ChatMessage.objects.get(id=message_id, sender=self.user)
        message.message = new_content
        message.save()

    @sync_to_async
    def delete_private_message(self, message_id):
        # Delete the message from the database
        ChatMessage.objects.filter(id=message_id, sender=self.user).delete()
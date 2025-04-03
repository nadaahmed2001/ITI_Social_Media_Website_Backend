from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Import models here to avoid early app loading
        from .models import GroupMessage
        data = json.loads(text_data)
        message = data['message']

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

    async def chat_message(self, event):
        # Send the message to WebSocket clients
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event["timestamp"],
        }))

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
        # Import models here to avoid early app loading
        from .models import ChatMessage
        from users.models import User
        data = json.loads(text_data)
        message = data['message']

        # Save the message to the database
        other_user = await User.objects.aget(id=self.other_user_id)
        await ChatMessage.objects.acreate(
            sender=self.user,
            receiver=other_user,
            message=message
        )

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

    async def chat_message(self, event):
        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))
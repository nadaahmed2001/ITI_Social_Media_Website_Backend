from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth.models import AnonymousUser
from .models import GroupChat, GroupMessage
from datetime import datetime

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.user = self.scope['user']

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        # Check if user is group member
        if not await GroupChat.objects.filter(id=self.group_id, members=self.user).aexists():
            await self.close()
            return

        self.room_group_name = f'group_{self.group_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        is_admin = await GroupChat.objects.filter(
            id=self.group_id, 
            supervisors=self.user
        ).aexists()

        # Save message to database
        group = await GroupChat.objects.aget(id=self.group_id)
        await GroupMessage.objects.acreate(
            group=group,
            sender=self.user,
            content=message
        )

        # Broadcast message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.user.username,
                'is_admin': is_admin,
                'timestamp': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'is_admin': event['is_admin'],
            'timestamp': event['timestamp']
        }))
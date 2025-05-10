import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import json
from datetime import datetime
from .models import GroupMessage, ChatMessage, GroupChat
from django.contrib.auth import get_user_model
User = get_user_model()  # Use custom user model instead of django.contrib.auth.models.User
import os
import django
from django.db.models import Q
from channels.db import database_sync_to_async
from django.db import close_old_connections
import traceback

logger = logging.getLogger(__name__)

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ITIHub.settings')
django.setup()

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.group_id = self.scope['url_route']['kwargs'].get('group_id')
            self.user = self.scope['user']
            
            # Set group_name early so disconnect can safely access it
            self.group_name = f"group_{self.group_id}"

            # Ensure the user is authenticated
            if self.user.is_anonymous:
                # Close the connection without sending any message
                logger.warning(f"Anonymous user tried to connect to group chat {self.group_id}")
                await self.close(code=4001)
                return

            # Check if user is a member of the group
            user_in_group = await self.is_user_in_group()
            if not user_in_group:
                logger.warning(f"User {self.user.id} tried to connect to group {self.group_id} but is not a member")
                await self.close(code=4003)
                return

            # Close any lingering connections before performing database operations
            await database_sync_to_async(close_old_connections)()

            # Add the user to the WebSocket group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
            # Notify the group of a new connection (optional)
            try:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "user_joined",
                        "username": self.user.username,
                        "user_id": self.user.id,
                        "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    }
                )
            except Exception as e:
                logger.error(f"Error sending user_joined notification: {e}")
        except Exception as e:
            logger.error(f"Error during GroupChat connection: {str(e)}")
            logger.error(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'group_name'):
                # Add timeout using asyncio.wait_for
                import asyncio
                try:
                    # Limit group_discard to 2 seconds
                    await asyncio.wait_for(
                        self.channel_layer.group_discard(self.group_name, self.channel_name),
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Group discard timed out for {self.group_name}")
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')  # Determine the action (send, edit, delete, clear)

            if action == 'send':
                message = data['message']
                # Save the message to the database
                msg_id = await self.save_group_message(message)
                # Broadcast the message to the group
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "sender": self.user.username,
                        "sender_id": self.user.id,
                        "message_id": msg_id,
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
                        "new_content": new_content,
                        "message_id": message_id,
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
            elif action == 'clear':
                # Clear all messages in the group chat
                await self.clear_group_messages()
                # Notify all clients in the group that the chat has been cleared
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "clear_chat",
                    }
                )
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'error': f"Message processing error: {str(e)}"
            }))

    async def chat_message(self, event):
        # Send the message to WebSocket clients
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "timestamp": event["timestamp"],
            "sender": event["sender"],
            "sender_id": event.get("sender_id"),
            "message_id": event.get("message_id")
        }))

    async def user_joined(self, event):
        # Notify clients of a new user joining
        await self.send(text_data=json.dumps({
            "event": "user_joined",
            "timestamp": event["timestamp"],
            "username": event["username"],
        }))

    async def user_left(self, event):
        # Notify clients of a user leaving
        await self.send(text_data=json.dumps({
            "event": "user_left",
            "timestamp": event["timestamp"],
            "username": event["username"],
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

    async def clear_chat(self, event):
        # Notify clients that the group chat has been cleared
        await self.send(text_data=json.dumps({
            "event": "clear_chat",
            "message": "Group chat has been cleared."
        }))

    @sync_to_async
    def save_group_message(self, message):
        # Save the message to the database
        try:
            msg = GroupMessage.objects.create(
                group_id=self.group_id,
                sender=self.user,
                content=message
            )
            logger.info(f"Message saved to group {self.group_id} by user {self.user.username}")
            return msg.id
        except Exception as e:
            logger.error(f"Error saving group message: {e}")
            logger.error(traceback.format_exc())
            raise

    @sync_to_async
    def edit_group_message(self, message_id, new_content):
        # Update the message in the database
        try:
            message = GroupMessage.objects.get(id=message_id, group_id=self.group_id)
            message.content = new_content
            message.save()
            logger.info(f"Message {message_id} edited in group {self.group_id}")
        except Exception as e:
            logger.error(f"Error editing group message: {e}")
            logger.error(traceback.format_exc())
            raise

    @sync_to_async
    def delete_group_message(self, message_id):
        # Delete the message from the database
        try:
            GroupMessage.objects.filter(id=message_id, group_id=self.group_id).delete()
            logger.info(f"Message {message_id} deleted from group {self.group_id}")
        except Exception as e:
            logger.error(f"Error deleting group message: {e}")
            logger.error(traceback.format_exc())
            raise

    @sync_to_async
    def clear_group_messages(self):
        # Delete all messages in the group chat from the database
        try:
            count = GroupMessage.objects.filter(group_id=self.group_id).count()
            GroupMessage.objects.filter(group_id=self.group_id).delete()
            logger.info(f"Cleared {count} messages from group {self.group_id}")
        except Exception as e:
            logger.error(f"Error clearing group messages: {e}")
            logger.error(traceback.format_exc())
            raise

    @database_sync_to_async
    def is_user_in_group(self):
        try:
            return GroupChat.objects.filter(id=self.group_id, members=self.user).exists()
        except Exception as e:
            logger.error(f"Error checking if user is in group: {e}")
            return False

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope['user']
            self.other_user_id = self.scope['url_route']['kwargs']['user_id']

            # Ensure the user is authenticated and has a valid id
            if self.user.is_anonymous or not hasattr(self.user, "id") or self.user.id is None:
                logger.warning("Anonymous user tried to connect to private chat")
                await self.close(code=4001)
                return

            # Validate the other user exists
            other_user_exists = await self.check_other_user_exists()
            if not other_user_exists:
                logger.warning(f"Attempted to chat with non-existent user ID: {self.other_user_id}")
                await self.close(code=4004)
                return

            # Create a unique room name for the private chat - set it early for disconnect method
            self.group_name = f'private_chat_{min(int(self.user.id), int(self.other_user_id))}_{max(int(self.user.id), int(self.other_user_id))}'

            # Close any lingering connections before performing database operations
            await database_sync_to_async(close_old_connections)()

            # Add the user to the WebSocket group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
            # Notify about connection
            logger.info(f"User {self.user.username} connected to private chat with user {self.other_user_id}")
        except Exception as e:
            logger.error(f"Error during PrivateChat connection: {str(e)}")
            logger.error(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'group_name'):
                # Add timeout using asyncio.wait_for
                import asyncio
                try:
                    # Limit group_discard to 2 seconds
                    await asyncio.wait_for(
                        self.channel_layer.group_discard(self.group_name, self.channel_name),
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Group discard timed out for {self.group_name}")
        except Exception as e:
            logger.error(f"Error in private chat disconnect: {e}")

    async def receive(self, text_data):
        try:
            # Close any lingering connections before performing database operations
            await database_sync_to_async(close_old_connections)()

            data = json.loads(text_data)
            action = data.get('action')  # Determine the action (send, edit, delete, clear)

            if action == 'send':
                message = data['message']
                # Save the message to the database
                msg_id = await self.save_private_message(message)
                # Broadcast the message to the other user
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': self.user.username,
                        'sender_id': self.user.id,
                        'timestamp': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        'id': msg_id  # Add ID so frontend can track the message
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
            elif action == 'clear':
                # Clear all messages in the private chat
                await self.clear_private_messages()
                # Notify both users in the private chat that the chat has been cleared
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "clear_chat",
                    }
                )
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'error': f"Message processing error: {str(e)}"
            }))

    async def chat_message(self, event):
        # Ensure the message is broadcast to all clients in the private chat
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event.get('sender_id'),
            'timestamp': event['timestamp'],
            'id': event.get('id')
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

    async def clear_chat(self, event):
        # Notify clients that the private chat has been cleared
        await self.send(text_data=json.dumps({
            "event": "clear_chat",
            "message": "Private chat has been cleared."
        }))

    @sync_to_async
    def save_private_message(self, message):
        # Save the message to the database
        try:
            other_user = User.objects.get(id=self.other_user_id)
            msg = ChatMessage.objects.create(
                sender=self.user,
                receiver=other_user,
                message=message
            )
            logger.info(f"Private message saved from {self.user.username} to user {self.other_user_id}")
            return msg.id
        except Exception as e:
            logger.error(f"Error saving private message: {e}")
            logger.error(traceback.format_exc())
            raise

    @sync_to_async
    def edit_private_message(self, message_id, new_content):
        # Update the message in the database
        try:
            message = ChatMessage.objects.get(id=message_id, sender=self.user)
            message.message = new_content
            message.save()
            logger.info(f"Private message {message_id} edited")
        except Exception as e:
            logger.error(f"Error editing private message: {e}")
            logger.error(traceback.format_exc())
            raise

    @sync_to_async
    def delete_private_message(self, message_id):
        # Delete the message from the database
        try:
            ChatMessage.objects.filter(id=message_id, sender=self.user).delete()
            logger.info(f"Private message {message_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting private message: {e}")
            logger.error(traceback.format_exc())
            raise

    @sync_to_async
    def clear_private_messages(self):
        # Delete all messages in the private chat from the database
        try:
            count = ChatMessage.objects.filter(
                Q(sender=self.user, receiver_id=self.other_user_id) |
                Q(sender_id=self.other_user_id, receiver=self.user)
            ).count()
            
            ChatMessage.objects.filter(
                Q(sender=self.user, receiver_id=self.other_user_id) |
                Q(sender_id=self.other_user_id, receiver=self.user)
            ).delete()
            
            logger.info(f"Cleared {count} messages between users {self.user.id} and {self.other_user_id}")
        except Exception as e:
            logger.error(f"Error clearing private messages: {e}")
            logger.error(traceback.format_exc())
            raise

    @database_sync_to_async
    def check_other_user_exists(self):
        try:
            return User.objects.filter(id=self.other_user_id).exists()
        except Exception as e:
            logger.error(f"Error checking if other user exists: {e}")
            return False
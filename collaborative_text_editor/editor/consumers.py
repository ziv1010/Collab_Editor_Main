# editor/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Document
from django.contrib.auth.models import User
import json
import random

class DocumentConsumer(AsyncWebsocketConsumer):
    active_users_dict = {}   # Class variable to keep track of active users

    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'
        self.user = self.scope["user"]
        self.color = await self.get_user_color(self.user.id)  # Assign a color to the user

        # Authenticate user
        if self.user.is_anonymous:
            await self.close()
        else:
            # Check if the user is a collaborator
            has_permission = await self.check_permission()
            if not has_permission:
                await self.close()
            else:
                # Add user to active users
                await self.add_active_user()

                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()

                # Send the initial content
                document = await self.get_document()
                content = json.loads(document.content) if document.content else {'ops': []}
                await self.send(text_data=json.dumps({
                    'type': 'init',
                    'content': content
                }))

                # Notify others about the new active user
                await self.broadcast_active_users()

    async def disconnect(self, close_code):
        # Remove user from active users
        await self.remove_active_user()

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Notify others about the user leaving
        await self.broadcast_active_users()

        # Remove cursor from other clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id
            }
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'content':
            content = data.get('content')
            if content:
                # Save the content
                await self.save_content(content)

                # Broadcast the content to other clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'document_change',
                        'content': content,
                        'sender_channel_name': self.channel_name
                    })
            else:
                # Handle cases where content is missing or invalid
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid content received.'
                }))
        elif message_type == 'cursor':
            range = data.get('range')
            if range is not None:
                # Broadcast cursor position to other clients
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'cursor_position',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'range': range,
                        'color': self.color,
                        'sender_channel_name': self.channel_name
                    }
                )

    # Receive content change from room group
    async def document_change(self, event):
        content = event['content']
        sender_channel_name = event['sender_channel_name']

        # Do not send the content back to the sender
        if self.channel_name != sender_channel_name:
            await self.send(text_data=json.dumps({
                'type': 'content',
                'content': content
            }))

    # Receive cursor position from room group
    async def cursor_position(self, event):
        sender_channel_name = event['sender_channel_name']

        # Do not send the cursor position back to the sender
        if self.channel_name != sender_channel_name:
            await self.send(text_data=json.dumps({
                'type': 'cursor',
                'user_id': event['user_id'],
                'username': event['username'],
                'range': event['range'],
                'color': event['color']
            }))

    # Handle user leaving
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id']
        }))

    # Broadcast active users list
    async def broadcast_active_users(self):
        active_users = await self.get_active_users()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'active_users',
                'users': active_users
            }
        )

    async def active_users(self, event):
        # Send active users list to client
        await self.send(text_data=json.dumps({
            'type': 'active_users',
            'users': event['users']
        }))

    @sync_to_async
    def get_document(self):
        return Document.objects.get(pk=self.document_id)

    @sync_to_async
    def check_permission(self):
        document = Document.objects.get(pk=self.document_id)
        return self.user in document.collaborators.all()

    @sync_to_async
    def save_content(self, content):
        # Load the document
        document = Document.objects.get(pk=self.document_id)
        # Save the content
        document.content = json.dumps(content)
        document.save()

    @sync_to_async
    def add_active_user(self):
        if self.room_group_name not in self.active_users_dict:
            self.active_users_dict[self.room_group_name] = {}
        self.active_users_dict[self.room_group_name][self.user.id] = {
            'username': self.user.username,
            'color': self.color
        }

    @sync_to_async
    def remove_active_user(self):
        if self.room_group_name in self.active_users_dict:
            self.active_users_dict[self.room_group_name].pop(self.user.id, None)
            if not self.active_users_dict[self.room_group_name]:
                del self.active_users_dict[self.room_group_name]

    @sync_to_async
    def get_active_users(self):
        users = []
        if self.room_group_name in self.active_users_dict:
            for user_id, info in self.active_users_dict[self.room_group_name].items():
                users.append({
                    'user_id': user_id,
                    'username': info['username'],
                    'color': info['color']
                })
        return users

    @sync_to_async
    def get_user_color(self, user_id):
        # Assign a consistent color based on user ID
        random.seed(user_id)
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF', '#FFFF00']
        return random.choice(colors)

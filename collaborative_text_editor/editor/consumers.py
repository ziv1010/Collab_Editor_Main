# editor/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Document
import json

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'

        # Authenticate user
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            # Check if the user is a collaborator
            has_permission = await self.check_permission()
            if not has_permission:
                await self.close()
            else:
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

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get('content')  # Extract content from the received data

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

    # Receive message from room group
    async def document_change(self, event):
        content = event['content']
        sender_channel_name = event['sender_channel_name']

        # Do not send the content back to the sender
        if self.channel_name != sender_channel_name:
            await self.send(text_data=json.dumps({
                'type': 'content',
                'content': content
            }))

    @sync_to_async
    def get_document(self):
        return Document.objects.get(pk=self.document_id)

    @sync_to_async
    def check_permission(self):
        document = Document.objects.get(pk=self.document_id)
        return self.scope["user"] in document.collaborators.all()

    @sync_to_async
    def save_content(self, content):
        # Load the document
        document = Document.objects.get(pk=self.document_id)
        # Save the content
        document.content = json.dumps(content)
        document.save()

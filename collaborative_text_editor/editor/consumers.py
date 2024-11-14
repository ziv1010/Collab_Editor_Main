# editor/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Document
import json
from delta import Delta

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'

        # Authenticate user
        if self.scope["user"].is_anonymous:
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
        delta = data  # Assuming data is the delta

        # Apply the delta and get the transformed delta
        transformed_delta = await self.apply_delta(delta)

        # Broadcast the transformed delta to other clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'document_change',
                'delta': transformed_delta,
                'sender_channel_name': self.channel_name
            }
        )

    # Receive message from room group
    async def document_change(self, event):
        delta = event['delta']
        sender_channel_name = event['sender_channel_name']

        # Do not send the delta back to the sender
        if self.channel_name != sender_channel_name:
            await self.send(text_data=json.dumps({
                'type': 'delta',
                'delta': delta
            }))

    @sync_to_async
    def get_document(self):
        return Document.objects.get(pk=self.document_id)

    @sync_to_async
    def apply_delta(self, delta):
        # Load the document
        document = Document.objects.get(pk=self.document_id)
        # Apply the delta to the document content
        content = json.loads(document.content) if document.content else {'ops': []}
        doc_delta = Delta(content)
        client_delta = Delta(delta)

        # Compose the new content
        new_content = doc_delta.compose(client_delta)

        # Save the new content
        document.content = json.dumps(new_content.ops)
        document.save()

        # Return the delta to send to other clients
        return delta

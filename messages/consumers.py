from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Message
from .serializers import MessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_name = self.get_room_name(self.user.id, self.other_user_id)
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = await self.create_message(data)
        serialized = MessageSerializer(message).data
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': serialized
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def create_message(self, data):
        from users.models import CustomUser
        sender = self.user
        recipient = CustomUser.objects.get(pk=self.other_user_id)
        return Message.objects.create(
            sender=sender,
            recipient=recipient,
            content=data.get('content', ''),
            image=data.get('image'),
            video=data.get('video')
        )

    def get_room_name(self, user1_id, user2_id):
        return f'chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}'

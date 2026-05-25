import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'chat_{self.group_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        is_member = await self.check_membership()
        if not is_member:
            await self.close()
            return

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
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        message_content = data.get('message', '').strip() if isinstance(data, dict) else ''

        if not message_content or len(message_content) > 2000:
            return

        message = await self.save_message(message_content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender': self.user.username,
                'timestamp': str(message.created_at),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def check_membership(self):
        from .models import ChatGroup
        return ChatGroup.objects.filter(
            id=self.group_id,
            members=self.user,
            is_active=True
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        from .models import ChatGroup, Message
        group = ChatGroup.objects.get(id=self.group_id)
        return Message.objects.create(
            group=group,
            sender=self.user,
            content=content
        )

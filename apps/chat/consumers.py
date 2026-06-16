import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.models import Conversation, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        user = await self._authenticate()
        if not user:
            await self.close()
            return

        self.scope["user"] = user
        can_join = await self._can_join(user)
        if not can_join:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

        await self._set_online(True)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )
        await self._set_online(False)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        msg_type = data.get("type", "message")

        if msg_type == "message":
            content = data.get("content", "").strip()
            if not content:
                return
            message = await self._save_message(self.scope["user"], content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "id": message.id,
                    "sender_id": self.scope["user"].id,
                    "sender_name": self.scope["user"].get_full_name(),
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                },
            )

        elif msg_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.scope["user"].id,
                    "user_name": self.scope["user"].get_full_name(),
                    "is_typing": data.get("is_typing", True),
                },
            )

        elif msg_type == "mark_read":
            await self._mark_messages_read(self.scope["user"])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "messages_read",
                    "user_id": self.scope["user"].id,
                },
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "id": event["id"],
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "content": event["content"],
            "timestamp": event["timestamp"],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
            "is_typing": event["is_typing"],
        }))

    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            "type": "mark_read",
            "user_id": event["user_id"],
        }))

    async def _authenticate(self):
        token_str = None
        query_string = self.scope.get("query_string", b"").decode()
        for param in query_string.split("&"):
            if param.startswith("token="):
                token_str = param.split("=", 1)[1]
                break
        if not token_str:
            return None
        try:
            access = AccessToken(token_str)
            user = await database_sync_to_async(User.objects.get)(id=access["user_id"])
            return user if user.is_active else None
        except Exception:
            return None

    async def _can_join(self, user):
        conv = await database_sync_to_async(
            lambda: Conversation.objects.only(
                "client_id", "agent_id"
            ).filter(id=self.conversation_id).first()
        )()
        if not conv:
            return False
        return user.id in (conv.client_id, conv.agent_id) or user.role == "admin"

    async def _set_online(self, is_online):
        user = self.scope["user"]
        await database_sync_to_async(
            lambda: User.objects.filter(id=user.id).update(is_online=is_online)
        )()

    async def _save_message(self, sender, content):
        conv = await database_sync_to_async(
            lambda: Conversation.objects.get(id=self.conversation_id)
        )()
        msg = await database_sync_to_async(Message.objects.create)(
            conversation=conv, sender=sender, content=content,
        )
        return msg

    async def _mark_messages_read(self, user):
        await database_sync_to_async(
            lambda: Message.objects.filter(
                conversation_id=self.conversation_id,
            ).exclude(sender=user).update(is_read=True)
        )()

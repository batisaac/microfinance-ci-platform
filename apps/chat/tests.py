import json

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.models import Conversation, Message

User = get_user_model()


class ChatAPITests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.agent_user = User.objects.create_user(
            email="agent@test.com", phone="0202020202",
            first_name="Agent", last_name="Test",
            password="pass1234", role="agent",
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", phone="0303030303",
            first_name="Admin", last_name="Test",
            password="pass1234", role="admin", is_staff=True,
        )
        self.conv_url = reverse("chat_conversations")

    def get_results(self, response):
        return response.data.get("results", response.data)

    def test_client_creates_conversation(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(self.conv_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["client_name"], "Client Test")

    def test_client_sees_own_conversations(self):
        Conversation.objects.create(client=self.client_user)
        other = User.objects.create_user(
            email="other@test.com", phone="0404040404",
            first_name="Other", last_name="Test",
            password="pass1234", role="client",
        )
        Conversation.objects.create(client=other)
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.conv_url)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_agent_sees_all_conversations(self):
        Conversation.objects.create(client=self.client_user)
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.get(self.conv_url)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_unauthenticated_cannot_create(self):
        response = self.client.post(self.conv_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_messages(self):
        conv = Conversation.objects.create(client=self.client_user)
        Message.objects.create(
            conversation=conv, sender=self.client_user,
            content="Bonjour",
        )
        self.client.force_authenticate(user=self.client_user)
        url = reverse("chat_messages", kwargs={"conversation_id": conv.id})
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "Bonjour")

    def test_client_cannot_access_other_conversation_messages(self):
        other = User.objects.create_user(
            email="other@test.com", phone="0505050505",
            first_name="Other", last_name="Test",
            password="pass1234", role="client",
        )
        conv = Conversation.objects.create(client=other)
        self.client.force_authenticate(user=self.client_user)
        url = reverse("chat_messages", kwargs={"conversation_id": conv.id})
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)

    def test_admin_assigns_agent(self):
        conv = Conversation.objects.create(client=self.client_user)
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("chat_assign", kwargs={"pk": conv.pk})
        response = self.client.patch(url, {"agent": self.agent_user.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conv.refresh_from_db()
        self.assertEqual(conv.agent, self.agent_user)


class ChatWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.agent_user = User.objects.create_user(
            email="agent@test.com", phone="0202020202",
            first_name="Agent", last_name="Test",
            password="pass1234", role="agent",
        )
        self.conv = Conversation.objects.create(
            client=self.client_user, agent=self.agent_user,
        )

    def _build_application(self):
        from apps.chat.routing import websocket_urlpatterns
        return URLRouter(websocket_urlpatterns)

    def _make_token(self, user):
        return str(AccessToken.for_user(user))

    async def test_connect_with_valid_token(self):
        token = self._make_token(self.client_user)
        communicator = WebsocketCommunicator(
            self._build_application(),
            f"/ws/chat/{self.conv.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_reject_connection_without_token(self):
        communicator = WebsocketCommunicator(
            self._build_application(),
            f"/ws/chat/{self.conv.id}/",
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_reject_connection_to_unknown_conversation(self):
        token = self._make_token(self.client_user)
        communicator = WebsocketCommunicator(
            self._build_application(),
            "/ws/chat/99999/?token={}".format(token),
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_send_and_receive_message(self):
        token = self._make_token(self.client_user)
        communicator = WebsocketCommunicator(
            self._build_application(),
            f"/ws/chat/{self.conv.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({"type": "message", "content": "Bonjour Agent!"})
        response = await communicator.receive_json_from(timeout=10)
        self.assertEqual(response["type"], "message")
        self.assertEqual(response["content"], "Bonjour Agent!")
        self.assertEqual(response["sender_name"], "Client Test")

        msg_db = await self._get_last_message()
        self.assertIsNotNone(msg_db)
        self.assertEqual(msg_db.content, "Bonjour Agent!")

        await communicator.disconnect()

    async def test_typing_indicator_broadcast(self):
        token = self._make_token(self.client_user)
        communicator = WebsocketCommunicator(
            self._build_application(),
            f"/ws/chat/{self.conv.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({"type": "typing", "is_typing": True})
        response = await communicator.receive_json_from(timeout=10)
        self.assertEqual(response["type"], "typing")
        self.assertTrue(response["is_typing"])

        await communicator.disconnect()

    async def test_mark_read_broadcast(self):
        from asgiref.sync import sync_to_async
        await sync_to_async(Message.objects.create)(
            conversation=self.conv, sender=self.client_user,
            content="Unread message",
        )
        token = self._make_token(self.agent_user)
        communicator = WebsocketCommunicator(
            self._build_application(),
            f"/ws/chat/{self.conv.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({"type": "mark_read"})
        response = await communicator.receive_json_from(timeout=10)
        self.assertEqual(response["type"], "mark_read")

        msg = await sync_to_async(Message.objects.get)(conversation=self.conv)
        self.assertTrue(msg.is_read)

        await communicator.disconnect()

    async def test_updates_online_status(self):
        token = self._make_token(self.client_user)
        communicator = WebsocketCommunicator(
            self._build_application(),
            f"/ws/chat/{self.conv.id}/?token={token}",
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        from asgiref.sync import sync_to_async
        user = await sync_to_async(User.objects.get)(id=self.client_user.id)
        self.assertTrue(user.is_online)

        await communicator.disconnect()

        user = await sync_to_async(User.objects.get)(id=self.client_user.id)
        self.assertFalse(user.is_online)

    async def _get_last_message(self):
        from asgiref.sync import sync_to_async
        return await sync_to_async(
            lambda: Message.objects.filter(conversation=self.conv).last()
        )()

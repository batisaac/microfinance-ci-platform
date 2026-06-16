from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.chat.models import Conversation, Message
from apps.chat.serializers import (
    ConversationCreateSerializer, ConversationListSerializer,
    ConversationAssignSerializer, MessageSerializer,
)
from apps.accounts.permissions import IsAdminOrAgent


class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.select_related("client", "agent").prefetch_related("messages")
        if user.role in ("admin", "agent"):
            return qs
        return qs.filter(client=user)

    def perform_create(self, serializer):
        conversation = serializer.save(client=self.request.user)
        self._auto_assign(conversation)

    def _auto_assign(self, conversation):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        agent = (
            User.objects.filter(role="agent", is_active=True)
            .exclude(agent_conversations__status="open")
            .order_by("agent_conversations__created_at")
            .first()
        )
        if not agent:
            agent = (
                User.objects.filter(role="agent", is_active=True)
                .order_by("agent_conversations__created_at")
                .first()
            )
        if agent:
            conversation.agent = agent
            conversation.save(update_fields=["agent"])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(None)
        instance = Conversation.objects.select_related("client", "agent").get(
            pk=serializer.data["id"]
        )
        out = ConversationListSerializer(instance, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)


class ConversationAssignView(generics.UpdateAPIView):
    serializer_class = ConversationAssignSerializer
    permission_classes = (permissions.IsAuthenticated & IsAdminOrAgent,)

    def get_queryset(self):
        return Conversation.objects.filter(status="open")

    def perform_update(self, serializer):
        serializer.save()


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        conv_id = self.kwargs["conversation_id"]
        user = self.request.user
        conv = Conversation.objects.filter(id=conv_id).first()
        if not conv:
            return Message.objects.none()
        if user.id not in (conv.client_id, conv.agent_id) and user.role != "admin":
            return Message.objects.none()
        return Message.objects.filter(conversation_id=conv_id).select_related("sender")

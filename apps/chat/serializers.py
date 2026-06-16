from rest_framework import serializers

from apps.chat.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("id", "sender", "sender_name", "content", "timestamp", "is_read")
        read_only_fields = ("id", "sender", "timestamp", "is_read")

    def get_sender_name(self, obj):
        return obj.sender.get_full_name()


class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ("id", "client", "agent", "status", "created_at", "updated_at")
        read_only_fields = ("id", "client", "agent", "status", "created_at", "updated_at")


class ConversationListSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id", "client_name", "agent_name", "status",
            "last_message", "unread_count",
            "created_at", "updated_at",
        )

    def get_client_name(self, obj):
        return obj.client.get_full_name()

    def get_agent_name(self, obj):
        return obj.agent.get_full_name() if obj.agent else None

    def get_last_message(self, obj):
        last = obj.messages.order_by("-timestamp").first()
        if last:
            return {
                "content": last.content[:100],
                "sender_name": last.sender.get_full_name(),
                "timestamp": last.timestamp,
            }
        return None

    def get_unread_count(self, obj):
        user = self.context["request"].user
        return obj.messages.exclude(sender=user).filter(is_read=False).count()


class ConversationAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ("agent",)

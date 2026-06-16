from rest_framework import serializers
from apps.notifications.models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id", "title", "body", "type",
            "link", "is_read", "created_at",
        )


class NotificationMarkReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("is_read",)

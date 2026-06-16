from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationListSerializer, NotificationMarkReadSerializer,
)
from apps.accounts.permissions import IsAdminOrAgent


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationListSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        qs = Notification.objects.filter(recipient=user)
        unread_only = self.request.query_params.get("unread", "").lower()
        if unread_only in ("true", "1"):
            qs = qs.filter(is_read=False)
        return qs


class NotificationMarkReadView(generics.UpdateAPIView):
    serializer_class = NotificationMarkReadSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user, is_read=False
        )

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(
            NotificationListSerializer(notification).data,
            status=status.HTTP_200_OK,
        )

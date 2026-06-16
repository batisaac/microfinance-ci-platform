from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "type", "is_read", "created_at")
    list_filter = ("is_read", "type")
    search_fields = ("recipient__email", "title", "body")
    readonly_fields = ("created_at",)

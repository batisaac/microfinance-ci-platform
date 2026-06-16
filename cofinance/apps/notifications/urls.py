from django.urls import path

from apps.notifications.views import NotificationListView, NotificationMarkReadView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification_list"),
    path("<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),
]

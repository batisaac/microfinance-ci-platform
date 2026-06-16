from django.urls import path

from apps.chat.views import (
    ConversationListCreateView, ConversationAssignView, MessageListView,
)

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="chat_conversations"),
    path("conversations/<int:pk>/assign/", ConversationAssignView.as_view(), name="chat_assign"),
    path("conversations/<int:conversation_id>/messages/", MessageListView.as_view(), name="chat_messages"),
]

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Ouverte"
        CLOSED = "closed", "Fermée"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="client_conversations", verbose_name="Client",
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="agent_conversations",
        verbose_name="Agent assigné",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.OPEN, verbose_name="Statut",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mise à jour le")

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"Conversation #{self.id} — {self.client.get_full_name()}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name="messages", verbose_name="Conversation",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="chat_messages", verbose_name="Expéditeur",
    )
    content = models.TextField(verbose_name="Message")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Envoyé le")
    is_read = models.BooleanField(default=False, verbose_name="Lu")

    class Meta:
        ordering = ("timestamp",)
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"Message #{self.id} — {self.sender.get_full_name()[:20]}"

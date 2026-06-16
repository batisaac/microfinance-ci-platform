from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Type(models.TextChoices):
        LOAN_STATUS = "loan_status", "Changement de statut du crédit"
        REPAYMENT = "repayment", "Remboursement enregistré"
        INSURANCE = "insurance", "Souscription d'assurance"
        SYSTEM = "system", "Notification système"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications", verbose_name="Destinataire",
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    body = models.TextField(verbose_name="Message")
    type = models.CharField(
        max_length=20, choices=Type.choices,
        default=Type.SYSTEM, verbose_name="Type",
    )
    link = models.CharField(max_length=500, blank=True, verbose_name="Lien")
    is_read = models.BooleanField(default=False, verbose_name="Lue")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.get_type_display()}] {self.title} — {self.recipient.get_full_name()}"

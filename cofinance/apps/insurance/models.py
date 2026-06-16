from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.conf import settings


class InsurancePlan(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    description = models.TextField(verbose_name="Description")
    coverage_amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Montant couvert"
    )
    monthly_premium = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prime mensuelle"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Produit d'assurance"
        verbose_name_plural = "Produits d'assurance"

    def __str__(self):
        return f"{self.name} — {self.monthly_premium} FCFA/mois"


class InsuranceSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expiree", "Expirée"
        CANCELLED = "annulee", "Annulée"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="insurance_subscriptions", verbose_name="Client",
    )
    plan = models.ForeignKey(
        InsurancePlan, on_delete=models.CASCADE,
        related_name="subscriptions", verbose_name="Produit",
    )
    loan = models.ForeignKey(
        "credits.Loan", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="insurance_subscriptions",
        verbose_name="Prêt associé",
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date d'expiration")
    duration_months = models.IntegerField(verbose_name="Durée (mois)")
    premium = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prime mensuelle"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.ACTIVE, verbose_name="Statut",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Souscrit le")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Souscription d'assurance"
        verbose_name_plural = "Souscriptions d'assurance"

    def __str__(self):
        return f"{self.client.get_full_name()} → {self.plan.name}"

    def is_expiring_soon(self, days=15):
        if self.status != self.Status.ACTIVE:
            return False
        return date.today() <= self.end_date <= date.today() + timedelta(days=days)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.premium = self.plan.monthly_premium
        super().save(*args, **kwargs)

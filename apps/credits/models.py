from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import date, timedelta


class Loan(models.Model):
    class Status(models.TextChoices):
        SOUMISE = "soumise", "Soumise"
        EN_ANALYSE = "en_analyse", "En analyse"
        APPROUVEE = "approuvee", "Approuvée"
        DECAISSEE = "decaissée", "Décaissée"
        REJETEE = "rejetee", "Rejetée"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="loans", verbose_name="Client"
    )
    analyzed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="analyzed_loans",
        verbose_name="Traité par"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant demandé")
    purpose = models.TextField(verbose_name="Objet du crédit")
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.SOUMISE, verbose_name="Statut"
    )
    eligibility_score = models.IntegerField(null=True, blank=True, verbose_name="Score d'éligibilité")
    duration_months = models.IntegerField(verbose_name="Durée (mois)")
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("5.00"),
        verbose_name="Taux d'intérêt mensuel (%)"
    )
    monthly_payment = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Mensualité"
    )
    agent_notes = models.TextField(blank=True, verbose_name="Notes de l'agent")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de soumission")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Demande de crédit"
        verbose_name_plural = "Demandes de crédit"

    def __str__(self):
        return f"Prêt #{self.id} - {self.client.get_full_name()} - {self.get_status_display()}"

    def calculate_score(self):
        ratio = self.amount / Decimal(self.duration_months)
        if ratio <= Decimal("50000"):
            return 100
        elif ratio <= Decimal("100000"):
            return 75
        elif ratio <= Decimal("200000"):
            return 50
        elif ratio <= Decimal("500000"):
            return 25
        return 10

    def generate_schedule(self):
        LoanSchedule.objects.filter(loan=self).delete()
        rate = self.interest_rate / Decimal(100)
        total = self.amount * (1 + rate * self.duration_months)
        self.monthly_payment = (total / self.duration_months).quantize(Decimal("0.01"))
        self.save(update_fields=["monthly_payment"])

        def add_months(source, months):
            month = source.month - 1 + months
            year = source.year + month // 12
            month = month % 12 + 1
            day = min(source.day, [31, 29 if year % 4 == 0 and (
                year % 100 != 0 or year % 400 == 0
            ) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            return date(year, month, day)

        base_date = date.today()
        for i in range(1, self.duration_months + 1):
            due = add_months(base_date, i)
            LoanSchedule.objects.create(
                loan=self,
                installment_number=i,
                due_date=due,
                amount=self.monthly_payment,
            )

    def save(self, *args, **kwargs):
        if not self.pk and not self.eligibility_score:
            self.eligibility_score = self.calculate_score()
        super().save(*args, **kwargs)


class LoanDocument(models.Model):
    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE,
        related_name="documents", verbose_name="Demande de prêt"
    )
    file = models.FileField(upload_to="loans/documents/%Y/%m/", verbose_name="Fichier")
    description = models.CharField(max_length=255, blank=True, verbose_name="Description")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'upload")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"Document #{self.id} - {self.description or 'Sans titre'}"


class LoanSchedule(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "À payer"
        PAID = "paid", "Payé"
        LATE = "late", "En retard"

    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE,
        related_name="schedule", verbose_name="Prêt"
    )
    installment_number = models.IntegerField(verbose_name="Numéro d'échéance")
    due_date = models.DateField(verbose_name="Date d'échéance")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Montant payé")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name="Statut")
    paid_date = models.DateField(null=True, blank=True, verbose_name="Date de paiement")

    class Meta:
        ordering = ("installment_number",)
        verbose_name = "Échéance"
        verbose_name_plural = "Échéances"

    def __str__(self):
        return f"Échéance #{self.installment_number} - Prêt #{self.loan.id}"

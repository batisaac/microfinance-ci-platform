from django.db import models
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from apps.credits.models import Loan, LoanSchedule


class Repayment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Espèces"
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        BANK_TRANSFER = "bank_transfer", "Virement bancaire"
        ORANGE_MONEY = "orange_money", "Orange Money"
        MTN_MOMO = "mtn_momo", "MTN MoMo"
        WAVE = "wave", "Wave"

    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE,
        related_name="repayments", verbose_name="Prêt"
    )
    schedule = models.ForeignKey(
        LoanSchedule, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="repayments",
        verbose_name="Échéance concernée"
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="recorded_repayments",
        verbose_name="Agent"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant payé")
    interest_paid = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Intérêts"
    )
    penalty_paid = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=Decimal("0.00"), verbose_name="Pénalité"
    )
    principal_paid = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Principal"
    )
    payment_date = models.DateField(default=date.today, verbose_name="Date de paiement")
    method = models.CharField(
        max_length=20, choices=Method.choices,
        default=Method.CASH, verbose_name="Mode de paiement"
    )
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Enregistré le")

    class Meta:
        ordering = ("-payment_date",)
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"

    def __str__(self):
        return f"Remboursement #{self.id} - Prêt #{self.loan.id} - {self.amount} FCFA"

    def _calculate_split(self, schedule):
        rate = self.loan.interest_rate / Decimal(100)
        interest = (schedule.amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        days_late = (self.payment_date - schedule.due_date).days
        penalty = Decimal("0.00")
        if days_late > 0:
            penalty = (schedule.amount * Decimal("0.005") * days_late).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        principal = (self.amount - interest - penalty).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if principal < 0:
            penalty = Decimal("0.00")
            interest = self.amount
            principal = Decimal("0.00")
        return interest, penalty, principal

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new and self.interest_paid is None:
            schedule_qs = LoanSchedule.objects.filter(
                loan=self.loan, status__in=("pending", "late")
            ).order_by("installment_number")
            if schedule_qs.exists():
                schedule = schedule_qs.first()
                self.schedule = schedule
                interest, penalty, principal = self._calculate_split(schedule)
                self.interest_paid = interest
                self.penalty_paid = penalty
                self.principal_paid = principal
                days_late = (self.payment_date - schedule.due_date).days
                if days_late > 0:
                    schedule.status = "late"
                schedule.paid_amount = (schedule.paid_amount or Decimal("0")) + self.amount
                if schedule.paid_amount >= schedule.amount:
                    schedule.status = "paid"
                    schedule.paid_date = self.payment_date
                schedule.save()
        super().save(*args, **kwargs)

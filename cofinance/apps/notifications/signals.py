from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.credits.models import Loan
from apps.repayments.models import Repayment
from apps.insurance.models import InsuranceSubscription
from apps.notifications.models import Notification


@receiver(pre_save, sender=Loan)
def _capture_old_loan_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Loan.objects.get(pk=instance.pk).status
        except Loan.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Loan)
def notify_loan_status_change(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.client,
            title="Demande de crédit soumise",
            body=(
                f"Votre demande de {instance.amount} FCFA "
                f"a été soumise avec succès."
            ),
            type=Notification.Type.LOAN_STATUS,
            link=f"/loans/{instance.id}/",
        )
        return

    old_status = getattr(instance, "_old_status", None)
    if old_status and old_status != instance.status:
        status_labels = {
            "soumise": "soumise",
            "en_analyse": "en cours d'analyse",
            "approuvee": "approuvée",
            "decaissée": "décaissée",
            "rejetee": "rejetée",
        }
        label = status_labels.get(instance.status, instance.status)
        Notification.objects.create(
            recipient=instance.client,
            title="Statut du crédit mis à jour",
            body=(
                f"Votre demande de crédit #{instance.id} "
                f"est désormais {label}."
            ),
            type=Notification.Type.LOAN_STATUS,
            link=f"/loans/{instance.id}/",
        )


@receiver(post_save, sender=Repayment)
def notify_repayment(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.loan.client,
            title="Remboursement enregistré",
            body=(
                f"Un remboursement de {instance.amount} FCFA "
                f"a été enregistré sur votre prêt #{instance.loan.id}."
            ),
            type=Notification.Type.REPAYMENT,
            link=f"/repayments/{instance.id}/",
        )


@receiver(post_save, sender=InsuranceSubscription)
def notify_insurance_subscription(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.client,
            title="Souscription assurance confirmée",
            body=(
                f"Votre souscription à {instance.plan.name} "
                f"est active jusqu'au {instance.end_date}."
            ),
            type=Notification.Type.INSURANCE,
            link="/insurance/my-policies/",
        )

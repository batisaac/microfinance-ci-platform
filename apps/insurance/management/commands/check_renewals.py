from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.insurance.models import InsuranceSubscription


class Command(BaseCommand):
    help = "Vérifie les souscriptions arrivant à expiration"

    def handle(self, *args, **options):
        today = date.today()
        expires_soon = today + timedelta(days=15)

        expiring = InsuranceSubscription.objects.filter(
            status=InsuranceSubscription.Status.ACTIVE,
            end_date__lte=expires_soon,
            end_date__gte=today,
        )

        for sub in expiring:
            self.stdout.write(
                f"[RENOUVELLEMENT] {sub.client.get_full_name()} – "
                f"{sub.plan.name} expire le {sub.end_date}."
            )

        self.stdout.write(self.style.SUCCESS(
            f"{expiring.count()} souscriptions arrivant à expiration dans 15 jours."
        ))

from datetime import date, timedelta
from decimal import Decimal
from random import randint, choice as random_choice

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.credits.models import Loan, LoanSchedule
from apps.repayments.models import Repayment
from apps.insurance.models import InsurancePlan, InsuranceSubscription
from apps.chat.models import Conversation, Message

User = get_user_model()

REGIONS = ["abidjan", "bouake", "korhogo", "daloa", "san_pedro", "yamoussoukro"]
FIRST_NAMES = ["Aminata", "Kouamé", "Fatou", "Mamadou", "Christine", "Léon", "Awa", "Yao", "Mariam"]
LAST_NAMES = ["Koné", "Traoré", "Diallo", "Kouassi", "N'Guessan", "Bamba", "Coulibaly", "Touré"]


class Command(BaseCommand):
    help = "Génère des données de démonstration pour COFINANCE CI"

    def handle(self, *args, **options):
        if User.objects.count() > 3:
            self.stdout.write(self.style.WARNING("La base contient déjà des données. Ignoré."))
            return

        with transaction.atomic():
            self._create_users()
            self._create_insurance_plans()
            self._create_loans()
            self._create_conversations()
        self.stdout.write(self.style.SUCCESS("Données de démonstration créées avec succès."))

    def _create_users(self):
        self.admin = User.objects.create_superuser(
            email="admin@cofinance.ci", password="admin123",
            first_name="Admin", last_name="COFINANCE", role="admin",
            phone="0100000000", region="abidjan",
        )
        self.agents = []
        for i in range(3):
            agent = User.objects.create_user(
                email=f"agent{i+1}@cofinance.ci",
                password="agent123",
                first_name=random_choice(FIRST_NAMES),
                last_name=random_choice(LAST_NAMES),
                role="agent",
                phone=f"010000000{i+1}",
                region=random_choice(REGIONS),
            )
            self.agents.append(agent)

        self.clients = []
        for i in range(5):
            client = User.objects.create_user(
                email=f"client{i+1}@cofinance.ci",
                password="client123",
                first_name=random_choice(FIRST_NAMES),
                last_name=random_choice(LAST_NAMES),
                role="client",
                phone=f"010000010{i}",
                region=random_choice(REGIONS),
            )
            self.clients.append(client)

        self._print_creds()

    def _print_creds(self):
        self.stdout.write("--- Identifiants de démonstration ---")
        self.stdout.write(f"  Admin  : admin@cofinance.ci / admin123")
        self.stdout.write(f"  Agent  : agent1@cofinance.ci / agent123")
        self.stdout.write(f"  Client : client1@cofinance.ci / client123")
        self.stdout.write("-------------------------------------")

    def _create_insurance_plans(self):
        plans_data = [
            ("Assurance Décès Accidentel", "Couverture en cas de décès accidentel", Decimal("500000"), Decimal("2500")),
            ("Assurance Invalidité", "Protection contre l'invalidité permanente", Decimal("1000000"), Decimal("5000")),
            ("Assurance Vie", "Couverture vie complète", Decimal("2000000"), Decimal("7500")),
        ]
        self.plans = []
        for name, desc, coverage, premium in plans_data:
            plan, _ = InsurancePlan.objects.get_or_create(
                name=name,
                defaults=dict(
                    description=desc,
                    coverage_amount=coverage,
                    monthly_premium=premium,
                ),
            )
            self.plans.append(plan)

    def _create_loans(self):
        loan_configs = [
            ("soumise", Decimal("150000"), 6, Decimal("5.00")),
            ("en_analyse", Decimal("250000"), 12, Decimal("5.00")),
            ("approuvee", Decimal("300000"), 6, Decimal("5.00")),
            ("decaissée", Decimal("500000"), 12, Decimal("5.00")),
            ("approuvee", Decimal("200000"), 3, Decimal("5.00")),
        ]
        for i, (status, amount, duration, rate) in enumerate(loan_configs):
            client = self.clients[i % len(self.clients)]
            agent = self.agents[i % len(self.agents)]
            loan = Loan.objects.create(
                client=client,
                amount=amount,
                purpose=random_choice([
                    "Achat de marchandises",
                    "Équipement agricole",
                    "Fonds de roulement",
                    "Rénovation boutique",
                    "Achat bétail",
                ]),
                duration_months=duration,
                interest_rate=rate,
                status=status,
                analyzed_by=agent if status in ("en_analyse", "approuvee", "decaissée") else None,
            )
            if status in ("approuvee", "decaissée"):
                loan.generate_schedule()
                if status == "decaissée":
                    self._create_repayments(loan, agent)

    def _create_repayments(self, loan, agent):
        schedules = LoanSchedule.objects.filter(loan=loan)
        for schedule in schedules:
            if schedule.installment_number <= 2:
                Repayment.objects.create(
                    loan=loan,
                    schedule=schedule,
                    agent=agent,
                    amount=schedule.amount,
                    payment_date=schedule.due_date - timedelta(days=randint(0, 2)),
                    method=random_choice(["mobile_money", "orange_money", "wave", "cash"]),
                )

    def _create_conversations(self):
        for client in self.clients[:3]:
            agent = self.agents[randint(0, len(self.agents) - 1)]
            conv = Conversation.objects.create(client=client, agent=agent)
            msg_count = randint(2, 5)
            for j in range(msg_count):
                sender = client if j % 2 == 0 else agent
                Message.objects.create(
                    conversation=conv,
                    sender=sender,
                    content=random_choice([
                        "Bonjour, j'ai une question sur mon prêt.",
                        "Quand est-ce que ma demande sera traitée ?",
                        "Merci pour votre aide !",
                        "Pouvez-vous m'envoyer le récapitulatif ?",
                        "Je n'ai pas reçu le décaissement.",
                        "Bien sûr, je vous envoie ça dans la journée.",
                        "Votre dossier est en cours d'analyse.",
                        "Le décaissement a été effectué hier.",
                        "N'hésitez pas si vous avez d'autres questions.",
                        "Je reviens vers vous rapidement.",
                    ]),
                )

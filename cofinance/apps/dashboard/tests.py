from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from apps.credits.models import Loan, LoanSchedule
from apps.repayments.models import Repayment
from apps.insurance.models import InsurancePlan, InsuranceSubscription

User = get_user_model()


class DashboardTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com", phone="0101010101",
            first_name="Admin", last_name="Test",
            password="pass1234", role="admin", is_staff=True,
        )
        self.agent = User.objects.create_user(
            email="agent@test.com", phone="0202020202",
            first_name="Agent", last_name="Test",
            password="pass1234", role="agent",
        )
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0303030303",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.url = reverse("dashboard")

        # Loan soumise
        self.loan1 = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("100000"),
            purpose="Test",
            duration_months=3,
            status="soumise",
        )
        # Loan décaissée
        self.loan2 = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("300000"),
            purpose="Test",
            duration_months=3,
            interest_rate=Decimal("5.00"),
            status="decaissée",
        )
        self.loan2.generate_schedule()
        self.schedule = LoanSchedule.objects.filter(loan=self.loan2).first()

        # Partiel — un remboursement sur la première échéance
        Repayment.objects.create(
            loan=self.loan2, agent=self.agent,
            amount=self.schedule.amount,
            payment_date=date.today(),
        )

        # Souscription active
        self.plan = InsurancePlan.objects.create(
            name="Test Plan",
            description="Test",
            coverage_amount=Decimal("500000"),
            monthly_premium=Decimal("5000"),
        )
        InsuranceSubscription.objects.create(
            client=self.client_user, plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            duration_months=1,
        )

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_forbidden(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_forbidden(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_has_all_fields(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("volume_par_statut", response.data)
        self.assertIn("taux_recouvrement", response.data)
        self.assertIn("souscriptions_actives", response.data)
        self.assertIn("conversations_ouvertes", response.data)

    def test_volume_by_status(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        vol = response.data["volume_par_statut"]
        self.assertEqual(vol.get("soumise"), 1)
        self.assertEqual(vol.get("decaissée"), 1)

    def test_recovery_rate_partial(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertGreater(response.data["taux_recouvrement"], 0)
        self.assertLess(response.data["taux_recouvrement"], 100)

    def test_recovery_rate_full(self):
        # Pay all schedules
        for s in LoanSchedule.objects.filter(loan=self.loan2):
            Repayment.objects.create(
                loan=self.loan2, agent=self.agent,
                amount=s.amount, payment_date=date.today(),
            )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.data["taux_recouvrement"], 100.0)

    def test_active_subscriptions_count(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.data["souscriptions_actives"], 1)

    def test_conversations_defaults_to_zero(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.data["conversations_ouvertes"], 0)

    def test_filter_by_agent(self):
        other_agent = User.objects.create_user(
            email="agent2@test.com", phone="0404040404",
            first_name="Agent2", last_name="Test",
            password="pass1234", role="agent",
        )
        # loan3 analyzed by other_agent
        Loan.objects.create(
            client=self.client_user,
            amount=Decimal("200000"),
            purpose="Test",
            duration_months=3,
            status="soumise",
            analyzed_by=other_agent,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"agent": other_agent.id})
        vol = response.data["volume_par_statut"]
        # Only the loan analyzed by other_agent
        self.assertEqual(vol.get("soumise"), 1)
        self.assertNotIn("decaissée", vol)

    def test_filter_by_region(self):
        region_user = User.objects.create_user(
            email="region@test.com", phone="0505050505",
            first_name="Region", last_name="Test",
            password="pass1234", role="client", region="korhogo",
        )
        Loan.objects.create(
            client=region_user,
            amount=Decimal("50000"),
            purpose="Test",
            duration_months=3,
            status="soumise",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"region": "korhogo"})
        vol = response.data["volume_par_statut"]
        self.assertEqual(vol.get("soumise"), 1)
        self.assertNotIn("decaissée", vol)

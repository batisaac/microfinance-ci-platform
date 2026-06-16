from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from apps.credits.models import Loan, LoanSchedule

User = get_user_model()


class LoanModelTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )

    def test_score_calculation_low_amount(self):
        loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("100000"),
            purpose="Commerce",
            duration_months=3,
        )
        self.assertGreaterEqual(loan.eligibility_score, 50)

    def test_score_calculation_high_amount(self):
        loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("2000000"),
            purpose="Commerce",
            duration_months=3,
        )
        self.assertLessEqual(loan.eligibility_score, 25)

    def test_schedule_generation(self):
        loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("300000"),
            purpose="Équipement",
            duration_months=3,
            interest_rate=Decimal("5.00"),
        )
        loan.generate_schedule()
        schedule = LoanSchedule.objects.filter(loan=loan)
        self.assertEqual(schedule.count(), 3)
        self.assertIsNotNone(loan.monthly_payment)


class LoanAPITests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.agent_user = User.objects.create_user(
            email="agent@test.com", phone="0202020202",
            first_name="Agent", last_name="Test",
            password="pass1234", role="agent",
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", phone="0303030303",
            first_name="Admin", last_name="Test",
            password="pass1234", role="admin", is_staff=True,
        )
        self.create_url = reverse("loan_list_create")
        self.valid_payload = {
            "amount": "250000",
            "purpose": "Achat de marchandises",
            "duration_months": 6,
        }

    def test_client_create_loan(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(self.create_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "soumise")

    def get_results(self, response):
        return response.data.get("results", response.data)

    def test_client_list_own_loans(self):
        Loan.objects.create(client=self.client_user, amount=100000, purpose="Test", duration_months=3)
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_client_cannot_see_other_loans(self):
        other = User.objects.create_user(
            email="other@test.com", phone="0404040404",
            first_name="Other", last_name="Test",
            password="pass1234", role="client",
        )
        Loan.objects.create(client=other, amount=100000, purpose="Test", duration_months=3)
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.create_url)
        self.assertEqual(len(self.get_results(response)), 0)

    def test_agent_can_see_all_loans(self):
        Loan.objects.create(client=self.client_user, amount=100000, purpose="Test", duration_months=3)
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.get(self.create_url)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_client_cannot_change_status(self):
        loan = Loan.objects.create(
            client=self.client_user, amount=100000,
            purpose="Test", duration_months=3,
        )
        self.client.force_authenticate(user=self.client_user)
        url = reverse("loan_status", kwargs={"pk": loan.pk})
        response = self.client.patch(url, {"status": "en_analyse"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_can_change_to_en_analyse(self):
        loan = Loan.objects.create(
            client=self.client_user, amount=100000,
            purpose="Test", duration_months=3,
        )
        self.client.force_authenticate(user=self.agent_user)
        url = reverse("loan_status", kwargs={"pk": loan.pk})
        response = self.client.patch(url, {"status": "en_analyse"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "en_analyse")

    def test_full_workflow_approval(self):
        loan = Loan.objects.create(
            client=self.client_user, amount=300000,
            purpose="Test", duration_months=3,
            interest_rate=Decimal("5.00"),
        )
        self.client.force_authenticate(user=self.agent_user)
        status_url = reverse("loan_status", kwargs={"pk": loan.pk})

        self.client.patch(status_url, {"status": "en_analyse"}, format="json")
        response = self.client.patch(status_url, {"status": "approuvee"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "approuvee")

        loan.refresh_from_db()
        schedules = LoanSchedule.objects.filter(loan=loan)
        self.assertEqual(schedules.count(), 3)

    def test_admin_can_disburse(self):
        loan = Loan.objects.create(
            client=self.client_user, amount=300000,
            purpose="Test", duration_months=3,
            interest_rate=Decimal("5.00"),
        )
        self.client.force_authenticate(user=self.admin_user)
        status_url = reverse("loan_status", kwargs={"pk": loan.pk})
        self.client.patch(status_url, {"status": "en_analyse"}, format="json")
        self.client.patch(status_url, {"status": "approuvee"}, format="json")
        response = self.client.patch(status_url, {"status": "decaissée"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "decaissée")

    def test_invalid_transition(self):
        loan = Loan.objects.create(
            client=self.client_user, amount=100000,
            purpose="Test", duration_months=3,
        )
        self.client.force_authenticate(user=self.agent_user)
        status_url = reverse("loan_status", kwargs={"pk": loan.pk})
        response = self.client.patch(status_url, {"status": "decaissée"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_create(self):
        response = self.client.post(self.create_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from apps.credits.models import Loan, LoanSchedule
from apps.repayments.models import Repayment

User = get_user_model()


class RepaymentModelTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("300000"),
            purpose="Commerce",
            duration_months=3,
            interest_rate=Decimal("5.00"),
            status="approuvee",
        )
        self.loan.generate_schedule()
        self.schedule = LoanSchedule.objects.filter(loan=self.loan).first()

    def test_interest_calculation(self):
        rate = self.loan.interest_rate / Decimal(100)
        expected = (self.schedule.amount * rate).quantize(Decimal("0.01"))
        repayment = Repayment.objects.create(
            loan=self.loan,
            amount=self.schedule.amount,
            payment_date=date.today(),
        )
        self.assertEqual(repayment.interest_paid, expected)

    def test_penalty_for_late_payment(self):
        past_date = self.schedule.due_date + timedelta(days=10)
        repayment = Repayment.objects.create(
            loan=self.loan,
            amount=self.schedule.amount,
            payment_date=past_date,
        )
        self.assertGreater(repayment.penalty_paid, Decimal("0"))

    def test_schedule_marked_paid(self):
        Repayment.objects.create(
            loan=self.loan,
            amount=self.schedule.amount,
            payment_date=date.today(),
        )
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.status, "paid")


class RepaymentAPITests(APITestCase):
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
        self.loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("300000"),
            purpose="Commerce",
            duration_months=3,
            interest_rate=Decimal("5.00"),
            status="approuvee",
        )
        self.loan.generate_schedule()
        self.list_url = reverse("repayment_list_create")
        self.valid_payload = {
            "loan": self.loan.id,
            "amount": "115000",
            "payment_date": str(date.today()),
            "method": "mobile_money",
        }

    def test_agent_can_create_repayment(self):
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.post(self.list_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

    def test_client_cannot_create_repayment(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(self.list_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_can_list_own_repayments(self):
        Repayment.objects.create(
            loan=self.loan, agent=self.agent_user,
            amount=Decimal("115000"), payment_date=date.today(),
        )
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_agent_can_list_all_repayments(self):
        Repayment.objects.create(
            loan=self.loan, agent=self.agent_user,
            amount=Decimal("115000"), payment_date=date.today(),
        )
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_unauthenticated_cannot_create(self):
        response = self.client.post(self.list_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_interest_penalty_in_response(self):
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.post(self.list_url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data.get("interest_paid"))
        self.assertIsNotNone(response.data.get("principal_paid"))

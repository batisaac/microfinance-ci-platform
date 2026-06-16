from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from apps.insurance.models import InsurancePlan, InsuranceSubscription

User = get_user_model()


class InsurancePlanModelTests(APITestCase):
    def setUp(self):
        self.plan = InsurancePlan.objects.create(
            name="Assurance Décès",
            description="Couverture décès accidentel",
            coverage_amount=Decimal("500000"),
            monthly_premium=Decimal("5000"),
        )

    def test_plan_str(self):
        self.assertIn("Assurance Décès", str(self.plan))
        self.assertIn("5000", str(self.plan))

    def test_plan_is_active_by_default(self):
        self.assertTrue(self.plan.is_active)


class InsuranceSubscriptionModelTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.plan = InsurancePlan.objects.create(
            name="Assurance Invalidité",
            description="Couverture invalidité",
            coverage_amount=Decimal("1000000"),
            monthly_premium=Decimal("7500"),
        )

    def test_is_expiring_soon_returns_true(self):
        sub = InsuranceSubscription.objects.create(
            client=self.client_user,
            plan=self.plan,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=10),
            duration_months=2,
            status=InsuranceSubscription.Status.ACTIVE,
        )
        self.assertTrue(sub.is_expiring_soon())

    def test_is_expiring_soon_false_when_expired(self):
        sub = InsuranceSubscription.objects.create(
            client=self.client_user,
            plan=self.plan,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() - timedelta(days=1),
            duration_months=2,
            status=InsuranceSubscription.Status.EXPIRED,
        )
        self.assertFalse(sub.is_expiring_soon())

    def test_premium_snapshots_on_create(self):
        sub = InsuranceSubscription.objects.create(
            client=self.client_user,
            plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            duration_months=1,
        )
        self.assertEqual(sub.premium, self.plan.monthly_premium)


class InsuranceAPITests(APITestCase):
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
        self.plan = InsurancePlan.objects.create(
            name="Assurance Décès",
            description="Couverture décès",
            coverage_amount=Decimal("500000"),
            monthly_premium=Decimal("5000"),
        )
        self.plans_url = reverse("insurance_plans")
        self.subscribe_url = reverse("insurance_subscribe")
        self.policies_url = reverse("insurance_my_policies")

    def get_results(self, response):
        return response.data.get("results", response.data)

    def test_list_active_plans(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.plans_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_list_plans_excludes_inactive(self):
        InsurancePlan.objects.create(
            name="Inactif", description="Inactif",
            coverage_amount=Decimal("100"), monthly_premium=Decimal("10"),
            is_active=False,
        )
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.plans_url)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_client_can_subscribe(self):
        self.client.force_authenticate(user=self.client_user)
        payload = {
            "plan": self.plan.id,
            "start_date": str(date.today()),
            "duration_months": 3,
        }
        response = self.client.post(self.subscribe_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "active")

    def test_subscribe_requires_auth(self):
        payload = {
            "plan": self.plan.id,
            "start_date": str(date.today()),
            "duration_months": 3,
        }
        response = self.client.post(self.subscribe_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscribe_sets_end_date(self):
        self.client.force_authenticate(user=self.client_user)
        payload = {
            "plan": self.plan.id,
            "start_date": "2026-07-01",
            "duration_months": 6,
        }
        response = self.client.post(self.subscribe_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["end_date"], "2027-01-01")

    def test_cannot_subscribe_to_inactive_plan(self):
        plan2 = InsurancePlan.objects.create(
            name="Inactif", description="Inactif",
            coverage_amount=Decimal("100"), monthly_premium=Decimal("10"),
            is_active=False,
        )
        self.client.force_authenticate(user=self.client_user)
        payload = {
            "plan": plan2.id,
            "start_date": str(date.today()),
            "duration_months": 3,
        }
        response = self.client.post(self.subscribe_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_sees_own_policies(self):
        InsuranceSubscription.objects.create(
            client=self.client_user, plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            duration_months=1,
        )
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.policies_url)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_agent_sees_all_policies(self):
        InsuranceSubscription.objects.create(
            client=self.client_user, plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            duration_months=1,
        )
        self.client.force_authenticate(user=self.agent_user)
        response = self.client.get(self.policies_url)
        self.assertEqual(len(self.get_results(response)), 1)

    def test_policy_detail_shows_expires_soon(self):
        sub = InsuranceSubscription.objects.create(
            client=self.client_user, plan=self.plan,
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() + timedelta(days=10),
            duration_months=1,
        )
        self.client.force_authenticate(user=self.client_user)
        detail_url = reverse("insurance_policy_detail", kwargs={"pk": sub.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["expires_soon"])

    def test_unauthenticated_cannot_list_policies(self):
        response = self.client.get(self.policies_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

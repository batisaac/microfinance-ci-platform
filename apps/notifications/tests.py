from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from apps.credits.models import Loan
from apps.repayments.models import Repayment
from apps.insurance.models import InsurancePlan, InsuranceSubscription
from apps.notifications.models import Notification

User = get_user_model()


class NotificationModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )

    def test_create_notification(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title="Test",
            body="Message de test",
        )
        self.assertFalse(notif.is_read)
        self.assertIsNotNone(notif.created_at)
        self.assertEqual(str(notif), "[Notification système] Test — Client Test")


class NotificationAutoCreationTests(APITestCase):
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

    def test_loan_creation_notification(self):
        loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("100000"),
            purpose="Test",
            duration_months=3,
        )
        notifs = Notification.objects.filter(recipient=self.client_user)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().type, Notification.Type.LOAN_STATUS)

    def test_loan_status_change_notification(self):
        loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("100000"),
            purpose="Test",
            duration_months=3,
        )
        Notification.objects.all().delete()
        loan.status = "en_analyse"
        loan.save()
        notifs = Notification.objects.filter(recipient=self.client_user)
        self.assertGreaterEqual(notifs.count(), 1)
        self.assertIn("en cours d'analyse", notifs.first().body)

    def test_repayment_notification(self):
        loan = Loan.objects.create(
            client=self.client_user,
            amount=Decimal("300000"),
            purpose="Test",
            duration_months=3,
            interest_rate=Decimal("5.00"),
            status="approuvee",
        )
        loan.generate_schedule()
        Notification.objects.all().delete()
        Repayment.objects.create(
            loan=loan, agent=self.agent_user,
            amount=Decimal("115000"),
            payment_date=date.today(),
        )
        notifs = Notification.objects.filter(recipient=self.client_user)
        self.assertGreaterEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().type, Notification.Type.REPAYMENT)

    def test_insurance_subscription_notification(self):
        plan = InsurancePlan.objects.create(
            name="Test Plan",
            description="Test",
            coverage_amount=Decimal("500000"),
            monthly_premium=Decimal("5000"),
        )
        sub = InsuranceSubscription.objects.create(
            client=self.client_user,
            plan=plan,
            start_date=date.today(),
            end_date=date.today(),
            duration_months=1,
        )
        notifs = Notification.objects.filter(recipient=self.client_user, type=Notification.Type.INSURANCE)
        self.assertEqual(notifs.count(), 1)
        self.assertIn(plan.name, notifs.first().body)


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="0101010101",
            first_name="Client", last_name="Test",
            password="pass1234", role="client",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", phone="0404040404",
            first_name="Other", last_name="Test",
            password="pass1234", role="client",
        )
        self.list_url = reverse("notification_list")

    def test_list_own_notifications(self):
        Notification.objects.create(
            recipient=self.client_user, title="A", body="Msg A",
        )
        Notification.objects.create(
            recipient=self.other_user, title="B", body="Msg B",
        )
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_filter_unread(self):
        Notification.objects.create(
            recipient=self.client_user, title="Unread", body="Unread",
        )
        n = Notification.objects.create(
            recipient=self.client_user, title="Read", body="Read",
            is_read=True,
        )
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(self.list_url, {"unread": "true"})
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Unread")

    def test_mark_as_read(self):
        notif = Notification.objects.create(
            recipient=self.client_user, title="Test", body="Test",
        )
        self.client.force_authenticate(user=self.client_user)
        url = reverse("notification_mark_read", kwargs={"pk": notif.pk})
        response = self.client.patch(url, {"is_read": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])

    def test_cannot_mark_other_users_notification(self):
        notif = Notification.objects.create(
            recipient=self.other_user, title="Test", body="Test",
        )
        self.client.force_authenticate(user=self.client_user)
        url = reverse("notification_mark_read", kwargs={"pk": notif.pk})
        response = self.client.patch(url, {"is_read": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

User = get_user_model()


class RegisterTests(APITestCase):
    def setUp(self):
        self.url = reverse("register")
        self.valid_payload = {
            "email": "jean@example.com",
            "phone": "0102030405",
            "first_name": "Jean",
            "last_name": "Kouamé",
            "region": "abidjan",
            "password": "pass1234",
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "jean@example.com")
        self.assertEqual(response.data["role"], "client")
        self.assertNotIn("password", response.data)

    def test_register_duplicate_email(self):
        self.client.post(self.url, self.valid_payload, format="json")
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post(self.url, {"email": "test@test.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        payload = {**self.valid_payload, "password": "abc"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_obtain_pair")
        self.password = "pass1234"
        self.user = User.objects.create_user(
            email="ama@example.com",
            phone="0506070809",
            first_name="Ama",
            last_name="Koné",
            password=self.password,
        )

    def test_login_success(self):
        response = self.client.post(self.url, {
            "email": "ama@example.com",
            "password": self.password,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {
            "email": "ama@example.com",
            "password": "wrongpass",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            phone="0101010101",
            first_name="Test",
            last_name="User",
            password="pass1234",
        )
        login_url = reverse("token_obtain_pair")
        res = self.client.post(login_url, {
            "email": "test@example.com",
            "password": "pass1234",
        }, format="json")
        self.refresh_token = res.data["refresh"]

    def test_refresh_success(self):
        url = reverse("token_refresh")
        response = self.client.post(url, {"refresh": self.refresh_token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class ProfileTests(APITestCase):
    def setUp(self):
        self.url = reverse("profile")
        self.user = User.objects.create_user(
            email="profile@example.com",
            phone="0202020202",
            first_name="Profil",
            last_name="Test",
            password="pass1234",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile@example.com")
        self.assertEqual(response.data["first_name"], "Profil")

    def test_update_profile(self):
        response = self.client.put(self.url, {
            "first_name": "Mis à jour",
            "last_name": "Nom",
            "phone": "0303030303",
            "region": "bouake",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Mis à jour")

    def test_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com", phone="1111111111",
            first_name="Admin", last_name="User",
            password="pass1234", role="admin", is_staff=True,
        )
        self.agent = User.objects.create_user(
            email="agent@test.com", phone="2222222222",
            first_name="Agent", last_name="User",
            password="pass1234", role="agent",
        )
        self.client_user = User.objects.create_user(
            email="client@test.com", phone="3333333333",
            first_name="Client", last_name="User",
            password="pass1234", role="client",
        )

    def test_admin_can_access_admin_endpoint(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_agent_can_access_profile(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_created_with_correct_role(self):
        url = reverse("register")
        payload = {
            "email": "newclient@test.com",
            "phone": "4444444444",
            "first_name": "New",
            "last_name": "Client",
            "password": "pass1234",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "client")

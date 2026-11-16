"""Tests for registration, login, email check and the guest command."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTRATION_DATA = {
    "fullname": "Example Username",
    "email": "example@mail.de",
    "password": "examplePassword",
    "repeated_password": "examplePassword",
}


class RegistrationTests(APITestCase):
    """POST /api/registration/"""

    url = reverse("registration")

    def test_registration_creates_user_and_returns_token(self):
        response = self.client.post(self.url, REGISTRATION_DATA, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data), {"token", "fullname", "email", "user_id"}
        )
        self.assertEqual(response.data["fullname"], "Example Username")
        self.assertTrue(User.objects.filter(email="example@mail.de").exists())

    def test_registration_with_different_passwords_fails(self):
        data = {**REGISTRATION_DATA, "repeated_password": "other"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_existing_email_fails(self):
        self.client.post(self.url, REGISTRATION_DATA, format="json")
        data = {**REGISTRATION_DATA, "email": "EXAMPLE@mail.de"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_blank_fullname_fails(self):
        data = {**REGISTRATION_DATA, "fullname": "   "}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_missing_fields_fails(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """POST /api/login/"""

    url = reverse("login")

    def setUp(self):
        self.client.post(
            reverse("registration"), REGISTRATION_DATA, format="json"
        )

    def test_login_returns_token(self):
        data = {"email": "example@mail.de", "password": "examplePassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "example@mail.de")
        self.assertIn("token", response.data)

    def test_login_with_wrong_password_fails(self):
        data = {"email": "example@mail.de", "password": "wrong"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_unknown_email_fails(self):
        data = {"email": "nobody@mail.de", "password": "examplePassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_inactive_user_fails(self):
        User.objects.filter(email="example@mail.de").update(is_active=False)
        data = {"email": "example@mail.de", "password": "examplePassword"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailCheckTests(APITestCase):
    """GET /api/email-check/"""

    url = reverse("email-check")

    def setUp(self):
        self.user = User.objects.create_user(
            username="max@example.com", email="max@example.com",
            password="pw123456", first_name="Max", last_name="Mustermann",
        )

    def test_email_check_requires_authentication(self):
        response = self.client.get(self.url, {"email": "max@example.com"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_check_returns_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {"email": "MAX@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "id": self.user.id, "email": "max@example.com",
            "fullname": "Max Mustermann",
        })

    def test_email_check_unknown_email_returns_404(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {"email": "no@example.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_email_check_invalid_email_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {"email": "not-an-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GuestUserCommandTests(APITestCase):
    """manage.py create_guest_user"""

    def test_command_creates_and_updates_guest(self):
        call_command("create_guest_user", stdout=StringIO())
        call_command("create_guest_user", stdout=StringIO())
        guest = User.objects.get(email="kevin@kovacsi.de")
        self.assertTrue(guest.check_password("asdasdasd"))

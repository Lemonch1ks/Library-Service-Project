from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class UserServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "password123"
        self.user = get_user_model().objects.create_user(
            email="reader@example.com",
            password=self.password,
            first_name="Read",
            last_name="Er",
        )

    def test_create_user_returns_201_and_hashes_password(self):
        response = self.client.post(
            reverse("users_service:create_user"),
            {
                "email": "new@example.com",
                "password": "safe-password-1",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

        created_user = get_user_model().objects.get(email="new@example.com")
        self.assertTrue(created_user.check_password("safe-password-1"))

    def test_user_detail_requires_authentication(self):
        response = self.client.get(reverse("users_service:user_detail"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_returns_authenticated_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse("users_service:user_detail"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], self.user.first_name)
        self.assertEqual(response.data["last_name"], self.user.last_name)

    def test_user_can_update_own_profile(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            reverse("users_service:user_detail"),
            {
                "first_name": "Updated",
                "last_name": "Reader",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Reader")

    def test_user_can_delete_own_profile(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse("users_service:user_detail"))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            get_user_model().objects.filter(pk=self.user.pk).exists()
        )

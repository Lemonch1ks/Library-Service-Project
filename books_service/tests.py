from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books_service.models import Book
from users_service.models import User


class BookServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="reader@example.com",
            password="password123",
            first_name="Read",
            last_name="Only",
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )
        self.book = Book.objects.create(
            title="Refactoring",
            author="Martin Fowler",
            cover=Book.BookCoverChoices.HARD,
            inventory=5,
            daily_fee="3.50",
        )
        self.list_url = reverse("books_service:book-list")

    def test_book_list_is_public(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.book.title)

    def test_book_detail_is_public(self):
        response = self.client.get(
            reverse("books_service:book-detail", args=[self.book.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.book.pk)


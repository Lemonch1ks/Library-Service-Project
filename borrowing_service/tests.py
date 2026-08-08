from datetime import date, timedelta

from django.test import RequestFactory, TestCase
from rest_framework import status

from books_service.models import Book
from borrowing_service.models import Borrowing
from borrowing_service.serializers import BorrowingCreateSerializer
from borrowing_service.views import BorrowingReturnView
from users_service.models import User


class BorrowingDateValidationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="reader@example.com",
            password="password123",
            first_name="Read",
            last_name="Er",
        )
        self.book = Book.objects.create(
            title="Domain-Driven Design",
            author="Eric Evans",
            cover=Book.BookCoverChoices.HARD,
            inventory=3,
            daily_fee="5.00",
        )

    def test_create_serializer_rejects_future_borrow_date(self):
        serializer = BorrowingCreateSerializer(
            data={
                "borrow_date": date.today() + timedelta(days=1),
                "expected_return_date": date.today() + timedelta(days=3),
                "book": self.book.id,
                "actual_return_date": date.today() + timedelta(days=2),
            },
            context={"request": self.factory.post("/borrowings/")},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["borrow_date"][0],
            "Borrow date cannot be in the future.",
        )
        self.assertNotIn("actual_return_date", serializer.validated_data)

    def test_create_serializer_rejects_expected_return_before_borrow_date(self):
        serializer = BorrowingCreateSerializer(
            data={
                "borrow_date": date.today(),
                "expected_return_date": date.today(),
                "book": self.book.id,
            },
            context={"request": self.factory.post("/borrowings/")},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["expected_return_date"][0],
            "Expected return date must be after borrow date.",
        )

    def test_return_view_rejects_return_before_borrow_date(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() + timedelta(days=1),
            expected_return_date=date.today() + timedelta(days=3),
        )
        request = self.factory.post(f"/borrowings/{borrowing.pk}/return/")
        request.user = self.user

        response_view = BorrowingReturnView.as_view()

        response = response_view(request, pk=borrowing.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["borrow_date"]),
            "Borrow date cannot be in the future.",
        )

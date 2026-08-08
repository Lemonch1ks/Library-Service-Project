from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, force_authenticate

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
        force_authenticate(request, user=self.user)

        response_view = BorrowingReturnView.as_view()

        response = response_view(request, pk=borrowing.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["borrow_date"]),
            "Borrow date cannot be in the future.",
        )


class BorrowingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="model@example.com",
            password="password123",
            first_name="Model",
            last_name="Tester",
        )
        self.book = Book.objects.create(
            title="Working Effectively with Legacy Code",
            author="Michael Feathers",
            cover=Book.BookCoverChoices.HARD,
            inventory=2,
            daily_fee="6.00",
        )

    def test_model_clean_rejects_future_borrow_date(self):
        borrowing = Borrowing(
            user=self.user,
            book=self.book,
            borrow_date=date.today() + timedelta(days=1),
            expected_return_date=date.today() + timedelta(days=2),
        )

        with self.assertRaises(ValidationError) as error:
            borrowing.full_clean()

        self.assertEqual(
            error.exception.message_dict["borrow_date"][0],
            "Borrow date cannot be in the future.",
        )

    def test_constraint_rejects_expected_return_on_or_before_borrow_date(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Borrowing.objects.create(
                    user=self.user,
                    book=self.book,
                    borrow_date=date.today(),
                    expected_return_date=date.today(),
                )

    def test_constraint_rejects_actual_return_before_borrow_date(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Borrowing.objects.create(
                    user=self.user,
                    book=self.book,
                    borrow_date=date.today(),
                    expected_return_date=date.today() + timedelta(days=2),
                    actual_return_date=date.today() - timedelta(days=1),
                )


class BorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            first_name="Main",
            last_name="Reader",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            first_name="Other",
            last_name="Reader",
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            first_name="Staff",
            last_name="Reader",
            is_staff=True,
        )
        self.book = Book.objects.create(
            title="Clean Architecture",
            author="Robert C. Martin",
            cover=Book.BookCoverChoices.SOFT,
            inventory=2,
            daily_fee="4.00",
        )
        self.list_url = reverse("borrowings_service:borrowing_list_create")

    def test_borrow_create_decrements_inventory(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.list_url,
            {
                "borrow_date": date.today(),
                "expected_return_date": date.today() + timedelta(days=7),
                "book": self.book.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        borrowing = Borrowing.objects.get(user=self.user, book=self.book)

        self.assertEqual(self.book.inventory, 1)
        self.assertEqual(borrowing.user, self.user)
        self.assertIsNone(borrowing.actual_return_date)

    def test_return_sets_actual_return_date_and_restores_inventory(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=3),
            expected_return_date=date.today() + timedelta(days=4),
        )
        self.book.inventory = 1
        self.book.save(update_fields=["inventory"])
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("borrowings_service:borrowing_return", args=[borrowing.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(borrowing.actual_return_date, date.today())
        self.assertEqual(self.book.inventory, 2)

    def test_non_owner_cannot_view_borrowing_detail(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=2),
            expected_return_date=date.today() + timedelta(days=5),
        )
        self.client.force_authenticate(self.other_user)

        response = self.client.get(
            reverse("borrowings_service:borrowing_detail", args=[borrowing.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_owner_cannot_return_someone_elses_borrowing(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=2),
            expected_return_date=date.today() + timedelta(days=5),
        )
        original_inventory = self.book.inventory
        self.client.force_authenticate(self.other_user)

        response = self.client.post(
            reverse("borrowings_service:borrowing_return", args=[borrowing.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        borrowing.refresh_from_db()
        self.book.refresh_from_db()

        self.assertIsNone(borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, original_inventory)

    def test_staff_can_view_another_users_borrowing_detail(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            borrow_date=date.today() - timedelta(days=1),
            expected_return_date=date.today() + timedelta(days=6),
        )
        self.client.force_authenticate(self.staff_user)

        response = self.client.get(
            reverse("borrowings_service:borrowing_detail", args=[borrowing.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.pk)

from datetime import date

from django.db import transaction
from rest_framework import serializers

from books_service.serializers import BookSerializer
from borrowing_service.models import Borrowing
from users_service.serializers import UserSerializer


def validate_borrowing_dates(
    borrow_date, expected_return_date, actual_return_date=None
):
    if borrow_date and borrow_date > date.today():
        raise serializers.ValidationError(
            {"borrow_date": "Borrow date cannot be in the future."}
        )

    if (
        borrow_date
        and expected_return_date
        and expected_return_date <= borrow_date
    ):
        raise serializers.ValidationError(
            {
                "expected_return_date": (
                    "Expected return date must be after borrow date."
                )
            }
        )

    if borrow_date and actual_return_date and actual_return_date < borrow_date:
        raise serializers.ValidationError(
            {
                "actual_return_date": (
                    "Actual return date must be after borrow date."
                )
            }
        )


class BorrowingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    borrow_date = serializers.DateField(required=True)
    expected_return_date = serializers.DateField(required=True)
    actual_return_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )

    def validate(self, attrs):
        borrow_date = attrs.get("borrow_date")
        expected_return_date = attrs.get("expected_return_date")
        actual_return_date = attrs.get("actual_return_date")

        validate_borrowing_dates(
            borrow_date=borrow_date,
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
        )
        return attrs


class BorrowingCreateSerializer(serializers.ModelSerializer):
    borrow_date = serializers.DateField(required=True)
    expected_return_date = serializers.DateField(required=True)
    actual_return_date = serializers.DateField(
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Borrowing
        fields = (
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
        )

    def validate(self, attrs):
        borrow_date = attrs.get("borrow_date")
        expected_return_date = attrs.get("expected_return_date")

        validate_borrowing_dates(
            borrow_date=borrow_date,
            expected_return_date=expected_return_date,
        )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        with transaction.atomic():
            book = validated_data["book"]

            if book.inventory <= 0:
                raise serializers.ValidationError(
                    {"book": "This book is not available."}
                )

            book.inventory -= 1
            book.save(update_fields=["inventory"])

            borrowing = Borrowing.objects.create(
                user=request.user,
                **validated_data,
            )

        return borrowing

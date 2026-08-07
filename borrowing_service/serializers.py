from rest_framework import serializers

from books_service.serializers import BookSerializer
from borrowing_service.models import Borrowing
from users_service.serializers import UserSerializer


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

class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )

    def create(self, validated_data):
        book = validated_data["book"]

        if book.inventory <= 0:
            raise serializers.ValidationError({"book": "This book is not available."})

        book.inventory -= 1
        book.save(update_fields=["inventory"])

        borrowing = Borrowing.objects.create(**validated_data)

        return borrowing

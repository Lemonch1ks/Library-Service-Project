from rest_framework import serializers

from books_service.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "Cover",
            "inventory",
            "Daily_fee",
        )

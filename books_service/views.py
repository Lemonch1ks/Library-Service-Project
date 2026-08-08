from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from permissions.permissions import IsAdminOrReadOnly

from books_service.models import Book
from books_service.serializers import BookSerializer


@extend_schema_view(
    list=extend_schema(
        auth=[],
        description="List all books. This endpoint is public.",
        responses={200: BookSerializer(many=True)},
    ),
    retrieve=extend_schema(
        auth=[],
        description="Retrieve a single book. This endpoint is public.",
        responses={200: BookSerializer},
    ),
    create=extend_schema(
        description="Create a new book. Staff users only.",
        responses={
            201: BookSerializer,
            403: OpenApiResponse(description="Staff users only."),
        },
    ),
    update=extend_schema(
        description="Replace a book record. Staff users only.",
        responses={
            200: BookSerializer,
            403: OpenApiResponse(description="Staff users only."),
        },
    ),
    partial_update=extend_schema(
        description="Partially update a book record. Staff users only.",
        responses={
            200: BookSerializer,
            403: OpenApiResponse(description="Staff users only."),
        },
    ),
    destroy=extend_schema(
        description="Delete a book record. Staff users only.",
        responses={
            204: OpenApiResponse(description="Book deleted."),
            403: OpenApiResponse(description="Staff users only."),
        },
    ),
)
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [
        IsAdminOrReadOnly,
    ]

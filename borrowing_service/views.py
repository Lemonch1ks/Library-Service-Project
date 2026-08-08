from datetime import date

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from django.db import transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response

from borrowing_service.models import Borrowing
from borrowing_service.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    validate_borrowing_dates,
)


@extend_schema_view(
    get=extend_schema(
        description=(
            "List borrowings visible to the authenticated user. "
            "Non-staff users only see their own borrowings. "
            "Staff users may inspect all borrowings and can filter by user."
        ),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by user id. Effective for staff users. "
                    "Non-staff users are still restricted to their own borrowings."
                ),
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by return state. "
                    "`true` returns borrowings with no `actual_return_date`; "
                    "`false` returns already returned borrowings."
                ),
            ),
        ],
        responses={
            200: BorrowingListSerializer(many=True),
            401: OpenApiResponse(description="Authentication required."),
        },
    ),
    post=extend_schema(
        description=(
            "Create a borrowing for the authenticated user. "
            "The selected book inventory is decreased by 1 when the book is available."
        ),
        request=BorrowingCreateSerializer,
        responses={
            201: BorrowingCreateSerializer,
            400: OpenApiResponse(
                description="Validation error or the selected book is not available."
            ),
            401: OpenApiResponse(description="Authentication required."),
        },
    ),
)
class BorrowingCreateListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Borrowing.objects.all()

    def get_queryset(self):
        queryset = Borrowing.objects.all()
        user_id = self.request.query_params.get("user_id", None)
        is_active = self.request.query_params.get("is_active", None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            queryset = queryset.filter(
                actual_return_date__isnull=is_active.lower() == "true"
            )

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        elif user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BorrowingListSerializer
        elif self.request.method == "POST":
            return BorrowingCreateSerializer


@extend_schema_view(
    get=extend_schema(
        description=(
            "Retrieve a borrowing visible to the authenticated user. "
            "Non-staff users can retrieve only their own borrowings; "
            "staff users can retrieve any borrowing."
        ),
        responses={
            200: BorrowingDetailSerializer,
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(
                description="Borrowing not found or not visible to this user."
            ),
        },
    )
)
class BorrowingDetailView(generics.RetrieveAPIView):
    serializer_class = BorrowingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Borrowing.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset


class BorrowingReturnView(generics.GenericAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = BorrowingDetailSerializer

    def get_queryset(self):
        queryset = Borrowing.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    @extend_schema(
        description=(
            "Return a borrowing visible to the authenticated user. "
            "No request body is required. "
            "This sets `actual_return_date` to today and increases the related "
            "book inventory by 1. Non-staff users can return only their own "
            "borrowings; staff users can return any borrowing."
        ),
        request=None,
        responses={
            200: BorrowingDetailSerializer,
            400: OpenApiResponse(
                description="Borrowing already returned or return date validation failed."
            ),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(
                description="Borrowing not found or not visible to this user."
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            raise serializers.ValidationError(
                {"detail": "This borrowing is already returned."}
            )

        with transaction.atomic():
            return_date = date.today()
            validate_borrowing_dates(
                borrow_date=borrowing.borrow_date,
                expected_return_date=borrowing.expected_return_date,
                actual_return_date=return_date,
            )
            borrowing.actual_return_date = return_date
            borrowing.save(update_fields=["actual_return_date"])

            book = borrowing.book
            book.inventory += 1
            book.save(update_fields=["inventory"])

        serializer = self.get_serializer(borrowing)

        return Response(serializer.data, status=status.HTTP_200_OK)

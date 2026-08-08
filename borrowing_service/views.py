from datetime import date

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

from django.urls import path

from borrowing_service.views import (
    BorrowingCreateListView,
    BorrowingDetailView,
    BorrowingReturnView,
)

app_name = "borrowings_service"

urlpatterns = [
    path("", BorrowingCreateListView.as_view(), name="borrowing_list_create"),
    path("<int:pk>/", BorrowingDetailView.as_view(), name="borrowing_detail"),
    path("<int:pk>/return/", BorrowingReturnView.as_view(), name="borrowing_return"),
]

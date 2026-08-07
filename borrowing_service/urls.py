from django.urls import path

from borrowing_service.views import BorrowingListView, BorrowingDetailView

app_name = "borrowings_service"

urlpatterns = [
    path("", BorrowingListView.as_view(), name="borrowing_list"),
    path("<int:pk>/", BorrowingDetailView.as_view(), name="borrowing_detail"),
]

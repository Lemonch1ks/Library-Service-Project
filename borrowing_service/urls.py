from django.urls import path

from borrowing_service.views import BorrowingRead

app_name = 'borrowings_service'

urlpatterns = [
    path('', BorrowingRead.as_view(), name='borrowing_read'),
]

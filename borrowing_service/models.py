from django.conf import settings
from django.db import models


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    book = models.ForeignKey(
        "books_service.Book",
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"User: {self.user.first_name} email: {self.user.email}, Book: {self.book.title}"
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(expected_return_date__gt=F("borrow_date")),
                name="expected_return_after_borrow_date",
            ),
            models.CheckConstraint(
                condition=Q(actual_return_date__isnull=True)
                | Q(actual_return_date__gte=F("borrow_date")),
                name="actual_return_on_or_after_borrow_date",
            ),
        ]

    def clean(self):
        super().clean()

        if self.borrow_date and self.borrow_date > date.today():
            raise ValidationError(
                {"borrow_date": "Borrow date cannot be in the future."}
            )

    def __str__(self):
        return (
            f"User: {self.user.first_name} "
            f"email: {self.user.email}, "
            f"Book: {self.book.title}"
        )

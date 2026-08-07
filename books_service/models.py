from django.core.validators import MinValueValidator
from django.db import models




class Book(models.Model):
    class BookCoverChoices(models.TextChoices):
        HARD = ('hard', 'Hard',)
        SOFT = ('soft', 'Soft',)

    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    Cover = models.CharField(
        max_length=100,
        choices=BookCoverChoices.choices,
    )
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    Daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title

from django.contrib import admin

from books_service import models

admin.site.register(models.Book)

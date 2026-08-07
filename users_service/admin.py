from django.contrib import admin

from users_service import models

admin.site.register(models.User)
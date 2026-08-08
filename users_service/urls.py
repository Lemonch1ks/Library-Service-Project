from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users_service.views import CreateUser, UserDetail

app_name = "users_service"

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", CreateUser.as_view(), name="create_user"),
    path("me/", UserDetail.as_view(), name="user_detail"),
]

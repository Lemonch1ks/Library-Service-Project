from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, mixins

from users_service.serializers import UserCreateSerializer, UserSerializer


class CreateUser(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserCreateSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import generics, permissions

from users_service.serializers import UserCreateSerializer, UserSerializer


@extend_schema(
    auth=[],
    description="Create a user account.",
    responses={201: UserCreateSerializer},
)
class CreateUser(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserCreateSerializer


@extend_schema_view(
    get=extend_schema(
        description="Retrieve the currently authenticated user's profile.",
        responses={200: UserSerializer, 401: OpenApiResponse(description="Authentication required.")},
    ),
    put=extend_schema(
        description="Replace the currently authenticated user's profile.",
        responses={200: UserSerializer, 401: OpenApiResponse(description="Authentication required.")},
    ),
    patch=extend_schema(
        description="Partially update the currently authenticated user's profile.",
        responses={200: UserSerializer, 401: OpenApiResponse(description="Authentication required.")},
    ),
    delete=extend_schema(
        description="Delete the currently authenticated user's profile.",
        responses={204: OpenApiResponse(description="User deleted."), 401: OpenApiResponse(description="Authentication required.")},
    ),
)
class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

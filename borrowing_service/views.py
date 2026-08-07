from rest_framework import generics, mixins

from borrowing_service.models import Borrowing
from borrowing_service.serializers import BorrowingReadSerializer


class BorrowingRead(
    generics.GenericAPIView, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingReadSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
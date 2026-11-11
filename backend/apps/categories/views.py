from django.db.models import ProtectedError
from rest_framework import permissions, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This category has transactions and cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

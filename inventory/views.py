# core/views.py
from rest_framework import viewsets, permissions
from .models import InventoryItem
from .serializers import InventoryItemSerializer

class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = InventoryItem.objects.all()
        if not user.is_superuser:
            qs = qs.filter(owner=user)  # 🔹 cada usuario ve solo lo suyo
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

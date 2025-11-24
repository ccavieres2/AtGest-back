# inventory/views.py
from rest_framework import viewsets, permissions
from .models import InventoryItem
from .serializers import InventoryItemSerializer
from accounts.utils import get_data_owner # 👈 Importar utilidad

class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = InventoryItem.objects.all()
        
        if not user.is_superuser:
            # 👈 Magia: Obtenemos el dueño real (puede ser el jefe)
            target_user = get_data_owner(user)
            qs = qs.filter(owner=target_user)
            
        return qs

    def perform_create(self, serializer):
        # 👈 Guardamos a nombre del jefe
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)
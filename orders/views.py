from rest_framework import viewsets, permissions
from .models import WorkOrder
from .serializers import WorkOrderSerializer
from accounts.utils import get_data_owner

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 1. Obtenemos al "Dueño real" de los datos.
        # Si soy Nelson (empleado), target_user será Iván (dueño).
        target_user = get_data_owner(self.request.user)
        
        # 2. Filtramos las órdenes usando ese usuario objetivo
        return WorkOrder.objects.filter(owner=target_user).order_by('-created_at')

    def perform_create(self, serializer):
        # 3. Al crear una orden, la guardamos a nombre del dueño, no del empleado.
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)
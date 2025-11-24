# clients/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from .models import Client, Vehicle
from .serializers import ClientSerializer, VehicleSerializer
from accounts.utils import get_data_owner

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'rut', 'email']

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return Client.objects.filter(owner=target_user).order_by('-created_at')

    def perform_create(self, serializer):
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)

# 👇 NUEVO VIEWSET PARA VEHÍCULOS
class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo mostramos vehículos de clientes que pertenecen a este taller
        target_user = get_data_owner(self.request.user)
        return Vehicle.objects.filter(client__owner=target_user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        # Verificamos que el cliente al que se le asigna el auto sea del taller
        client_id = request.data.get('client')
        target_user = get_data_owner(request.user)
        
        try:
            client = Client.objects.get(id=client_id, owner=target_user)
        except Client.DoesNotExist:
            return Response({"error": "Cliente no válido o no te pertenece."}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)
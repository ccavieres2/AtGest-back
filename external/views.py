# external/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied # 👈 Faltaba esta importación
from django.db.models import Q

from .models import ExternalService, ServiceRequest
from .serializers import ExternalServiceSerializer, ServiceRequestSerializer
from accounts.utils import get_data_owner

# Permiso personalizado mejorado
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    - Leer: Cualquiera autenticado.
    - Crear: Solo usuarios con rol 'owner'.
    - Editar/Borrar: Solo el Dueño que CREÓ el servicio.
    """
    def has_permission(self, request, view):
        # 1. Permiso a nivel de Vista (General)
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Para escribir (POST), debes ser 'owner'
        if hasattr(request.user, 'profile') and request.user.profile.role == 'owner':
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # 2. Permiso a nivel de Objeto (Específico)
        if request.method in permissions.SAFE_METHODS:
            return True # Cualquiera puede ver el detalle

        # Para editar/borrar, el dueño del objeto debe ser el mismo que el usuario actual (o su jefe)
        return obj.owner == get_data_owner(request.user)

class ExternalServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ExternalServiceSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        # 🟢 CAMBIO CLAVE: Ahora retornamos TODO para que sea un Mercado
        return ExternalService.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.role != 'owner':
            raise PermissionDenied("Solo los dueños pueden crear servicios.")
            
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)

# 👇 NUEVO VIEWSET PARA SOLICITUDES B2B
class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        # Muestra solicitudes enviadas (requester) O recibidas (provider)
        return ServiceRequest.objects.filter(
            Q(requester=target_user) | Q(provider=target_user)
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        Endpoint para que el proveedor (Carlos) acepte o rechace el trabajo.
        """
        service_req = self.get_object()
        target_user = get_data_owner(request.user)

        # Validación de seguridad: Solo el proveedor puede responder
        if service_req.provider != target_user:
            return Response({"error": "No tienes permiso para gestionar esta solicitud."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        
        # Validación de estados permitidos
        if new_status not in ['accepted', 'rejected', 'completed']:
             return Response({"error": "Estado no válido."}, status=status.HTTP_400_BAD_REQUEST)

        service_req.status = new_status
        service_req.save()
        return Response({"status": "updated", "new_status": new_status})
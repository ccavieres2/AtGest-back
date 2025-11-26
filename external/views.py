# external/views.py
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import ExternalService
from .serializers import ExternalServiceSerializer
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
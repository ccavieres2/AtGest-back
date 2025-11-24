# externalService/views.py
from rest_framework import viewsets, permissions
from .models import ExternalService
from .serializers import ExternalServiceSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from accounts.utils import get_data_owner # 👈 Importar utilidad

# 👈 Permiso personalizado actualizado para External Services
class IsOwnerOrEmployeeOrReadOnly(permissions.BasePermission):
    """
    Lectura para todos.
    Escritura solo para el dueño o sus empleados.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Verificar si el usuario actual (o su jefe) es el dueño del objeto
        data_owner = get_data_owner(request.user)
        return obj.owner == data_owner

class ExternalServiceViewSet(viewsets.ModelViewSet):
    # El marketplace es público para VER, pero privado para EDITAR
    queryset = ExternalService.objects.all()
    serializer_class = ExternalServiceSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    # 👈 Usamos el permiso actualizado
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrEmployeeOrReadOnly]

    def perform_create(self, serializer):
        # 👈 Si un mecánico publica un servicio, queda a nombre del taller (el jefe)
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)
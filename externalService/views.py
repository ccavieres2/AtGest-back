# atgest-back/externalService/views.py
from rest_framework import viewsets, permissions
from .models import ExternalService
from .serializers import ExternalServiceSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import IsOwnerOrReadOnly  # 👈 1. Importa el nuevo permiso

class ExternalServiceViewSet(viewsets.ModelViewSet):
    # 👇 2. El queryset base ahora es a TODOS los servicios
    queryset = ExternalService.objects.all()
    serializer_class = ExternalServiceSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    # 👇 3. Cambia los permisos
    # IsAuthenticated: Asegura que DEBES estar logueado para VER el marketplace.
    # IsOwnerOrReadOnly: Se encarga de que solo el dueño pueda EDITAR o BORRAR.
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        # 🔥 Esto asigna el owner al crear (está perfecto)
        serializer.save(owner=self.request.user)

    # 👇 4. ¡ELIMINA O COMENTA ESTA FUNCIÓN!
    # Ya no queremos filtrar por usuario, queremos que todos vean todo.
    #
    # def get_queryset(self):
    #     # 🔐 Solo muestra los servicios del usuario autenticado (ESTO SE ELIMINA)
    #     return ExternalService.objects.filter(owner=self.request.user)
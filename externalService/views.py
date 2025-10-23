# externalService/views.py
from rest_framework import viewsets, permissions
from .models import ExternalService
from .serializers import ExternalServiceSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class ExternalServiceViewSet(viewsets.ModelViewSet):
    queryset = ExternalService.objects.all()
    serializer_class = ExternalServiceSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # 🔥 Aquí se asigna automáticamente el owner
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        # 🔐 Solo muestra los servicios del usuario autenticado
        return ExternalService.objects.filter(owner=self.request.user)

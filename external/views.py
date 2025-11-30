# external/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import ExternalService, ServiceRequest, Message # 👈 Importar Message
from .serializers import ExternalServiceSerializer, ServiceRequestSerializer, MessageSerializer # 👈 Importar MessageSerializer
from accounts.utils import get_data_owner

# ... (IsOwnerOrReadOnly se mantiene igual) ...
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        if hasattr(request.user, 'profile') and request.user.profile.role == 'owner':
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == get_data_owner(request.user)

# ... (ExternalServiceViewSet se mantiene igual) ...
class ExternalServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ExternalServiceSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return ExternalService.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'profile') or self.request.user.profile.role != 'owner':
            raise PermissionDenied("Solo los dueños pueden crear servicios.")
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)

# ... (ServiceRequestViewSet se mantiene igual) ...
class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return ServiceRequest.objects.filter(
            Q(requester=target_user) | Q(provider=target_user)
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        service_req = self.get_object()
        target_user = get_data_owner(request.user)

        if service_req.provider != target_user:
            return Response({"error": "No tienes permiso."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if new_status not in ['accepted', 'rejected', 'completed']:
             return Response({"error": "Estado no válido."}, status=status.HTTP_400_BAD_REQUEST)

        service_req.status = new_status
        service_req.save()
        return Response({"status": "updated", "new_status": new_status})

# 👇 AQUÍ ESTABA EL ERROR: CORRECCIÓN DEL MESSAGE VIEWSET
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        
        # Filtramos mensajes donde soy parte de la solicitud
        queryset = Message.objects.filter(
            Q(service_request__requester=target_user) | 
            Q(service_request__provider=target_user)
        )

        request_id = self.request.query_params.get('request_id')
        if request_id:
            queryset = queryset.filter(service_request_id=request_id)
            
        return queryset

    def perform_create(self, serializer):
        # 1. Obtener ID de la solicitud
        request_id = self.request.data.get('service_request')
        if not request_id:
            raise ValidationError({"service_request": "Este campo es obligatorio."})

        # 2. Obtener la solicitud y validar permisos
        service_req = get_object_or_404(ServiceRequest, id=request_id)
        target_user = get_data_owner(self.request.user)

        # 3. Verificar si el usuario (o su jefe) es parte de la conversación
        if target_user != service_req.requester and target_user != service_req.provider:
            raise PermissionDenied("No tienes permiso para participar en este chat.")

        # 4. Guardar el mensaje
        serializer.save(sender=self.request.user)
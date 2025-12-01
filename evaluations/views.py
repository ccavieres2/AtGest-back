from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction 

# Importaciones de modelos y serializers
from .models import Evaluation, EvaluationItem
from .serializers import EvaluationSerializer, EvaluationItemSerializer
from orders.models import WorkOrder
from external.models import ServiceRequest  # 👈 Importante para el módulo B2B
from accounts.models import Notification    # 👈 NUEVO: Importar modelo de Notificación
from accounts.utils import get_data_owner

class EvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return Evaluation.objects.filter(owner=target_user).order_by('-created_at')

    def perform_create(self, serializer):
        target_user = get_data_owner(self.request.user)
        # Validación básica para no duplicar evaluaciones activas
        vehicle = serializer.validated_data.get('vehicle')
        if vehicle:
            active_statuses = ['draft', 'sent', 'approved']
            exists = Evaluation.objects.filter(
                vehicle=vehicle, 
                status__in=active_statuses
            ).exists()
            if exists:
                raise ValidationError({"vehicle": "Este vehículo ya tiene una evaluación en curso."})
        
        serializer.save(owner=target_user)

    @action(detail=True, methods=['post'])
    def update_items(self, request, pk=None):
        """
        Recibe la lista de ítems del frontend y los actualiza.
        Aquí es donde guardamos el vínculo con el servicio externo (externalId).
        """
        evaluation = self.get_object()
        items_data = request.data.get('items', [])
        
        # Borramos los ítems viejos para sobrescribir con los nuevos
        EvaluationItem.objects.filter(evaluation=evaluation).delete()
        
        new_items = []
        for item in items_data:
            # 👇 Capturamos el ID del servicio externo si viene del frontend
            external_id = item.get('externalId') 
            
            new_items.append(EvaluationItem(
                evaluation=evaluation,
                description=item.get('description'),
                price=item.get('price', 0),
                is_approved=item.get('is_approved', True),
                # 👇 Guardamos la referencia en la base de datos
                external_service_source_id=external_id 
            ))
        
        EvaluationItem.objects.bulk_create(new_items)
        return Response({'status': 'items updated'})

    @action(detail=True, methods=['post'])
    def generate_order(self, request, pk=None):
        """
        Aprueba la evaluación, crea la Orden de Trabajo y envía las solicitudes B2B.
        """
        evaluation = self.get_object()

        # 1. Validaciones
        if hasattr(evaluation, 'work_order'):
            return Response({"error": "Ya existe una Orden de Trabajo para esta evaluación."}, status=status.HTTP_400_BAD_REQUEST)

        approved_items = evaluation.items.filter(is_approved=True)
        if not approved_items.exists():
            return Response({"error": "La evaluación no tiene ítems aprobados."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Proceso Transaccional (Todo o nada)
        try:
            with transaction.atomic():
                # A. Actualizar estado Evaluación
                evaluation.status = 'approved'
                evaluation.save()

                # B. Crear Orden de Trabajo (OT)
                work_order = WorkOrder.objects.create(
                    evaluation=evaluation,
                    owner=evaluation.owner,
                    status='pending',
                    internal_notes=f"Generada desde Evaluación #{evaluation.id}"
                )

                # C. Lógica de Externalización (B2B) 
                # Recorremos los ítems aprobados para ver si alguno es un servicio externo
                for item in approved_items:
                    if item.external_service_source:
                        service = item.external_service_source
                        
                        # Si tiene un servicio externo vinculado, creamos la solicitud para el otro taller
                        ServiceRequest.objects.create(
                            requester=evaluation.owner,               # Quien pide (Tu usuario/Ivan)
                            provider=service.owner,                   # Quien provee (El otro taller/Carlos)
                            service=service,                          # El servicio específico
                            related_order_id=work_order.id            # Referencia a la OT
                        )

                        # 👇👇 NUEVO: Crear la Notificación para el Proveedor 👇👇
                        Notification.objects.create(
                            recipient=service.owner, # El dueño del servicio externo (Carlos)
                            message=f"¡Nueva Solicitud! Taller {evaluation.owner.username} requiere: {service.name}",
                            link="/requests" # Para que al hacer clic vaya a la bandeja de entrada
                        )
                        # 👆👆 FIN DE LO NUEVO 👆👆

            return Response({
                "message": "Orden creada y solicitudes enviadas correctamente", 
                "order_id": work_order.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"ERROR GENERANDO ORDEN: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# evaluations/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction 

from .models import Evaluation, EvaluationItem
from .serializers import EvaluationSerializer, EvaluationItemSerializer
from orders.models import WorkOrder
from external.models import ServiceRequest
from accounts.models import Notification
from accounts.utils import get_data_owner
# Importamos Product para la validación de stock
from inventory.models import Product

class EvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return Evaluation.objects.filter(owner=target_user).order_by('-folio')

    def perform_create(self, serializer):
        target_user = get_data_owner(self.request.user)
        vehicle = serializer.validated_data.get('vehicle')
        if vehicle:
            active_statuses = ['draft', 'sent', 'approved']
            exists = Evaluation.objects.filter(
                vehicle=vehicle, 
                status__in=active_statuses
            ).exists()
            if exists:
                raise ValidationError({"vehicle": "Este vehículo ya tiene una evaluación en curso."})
        
        serializer.save(owner=target_user, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def update_items(self, request, pk=None):
        evaluation = self.get_object()
        items_data = request.data.get('items', [])
        
        # Borramos los ítems anteriores para reescribirlos
        EvaluationItem.objects.filter(evaluation=evaluation).delete()
        
        new_items = []
        for item in items_data:
            external_id = item.get('externalId') 
            inventory_id = item.get('inventoryId')
            qty = item.get('qty', 1)
            
            new_items.append(EvaluationItem(
                evaluation=evaluation,
                description=item.get('description'),
                price=item.get('price', 0),
                is_approved=item.get('is_approved', True),
                external_service_source_id=external_id,
                inventory_item_id=inventory_id,
                quantity=qty
            ))
        
        EvaluationItem.objects.bulk_create(new_items)
        return Response({'status': 'items updated'})

    @action(detail=True, methods=['post'])
    def generate_order(self, request, pk=None):
        evaluation = self.get_object()

        if hasattr(evaluation, 'work_order'):
            return Response({"error": "Ya existe una Orden de Trabajo para esta evaluación."}, status=status.HTTP_400_BAD_REQUEST)

        approved_items = evaluation.items.filter(is_approved=True)
        if not approved_items.exists():
            return Response({"error": "La evaluación no tiene ítems aprobados."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. Cambiar estado a aprobado
                evaluation.status = 'approved'
                evaluation.save()

                # 2. Crear la Orden de Trabajo
                work_order = WorkOrder.objects.create(
                    evaluation=evaluation,
                    owner=evaluation.owner,
                    folio=evaluation.folio,
                    status='pending',
                    internal_notes=f"Generada desde Evaluación #{evaluation.folio}"
                )

                # 3. Procesar los ítems
                for item in approved_items:
                    # A) Solicitudes Externas
                    if item.external_service_source:
                        service = item.external_service_source
                        ServiceRequest.objects.create(
                            requester=evaluation.owner,
                            provider=service.owner,
                            service=service,
                            related_order_id=work_order.id
                        )
                        Notification.objects.create(
                            recipient=service.owner,
                            message=f"¡Nueva Solicitud! Taller {evaluation.owner.username} requiere: {service.name}",
                            link="/requests"
                        )

                    # B) Descuento de Inventario (Lógica FIFO por Lotes)
                    if item.inventory_item:
                        product_ref = item.inventory_item # Esto es un Product
                        qty_needed = item.quantity
                        
                        # Buscamos lotes con stock > 0, ordenados por vencimiento (el más viejo primero)
                        batches = product_ref.batches.filter(current_quantity__gt=0).order_by('expiration_date', 'entry_date')
                        
                        for batch in batches:
                            if qty_needed <= 0:
                                break
                            
                            if batch.current_quantity >= qty_needed:
                                # El lote alcanza para cubrir todo lo que falta
                                batch.current_quantity -= qty_needed
                                batch.save()
                                qty_needed = 0
                            else:
                                # El lote se agota, tomamos todo lo que tiene y seguimos buscando
                                qty_needed -= batch.current_quantity
                                batch.current_quantity = 0
                                batch.save()
                        
                        if qty_needed > 0:
                            print(f"ALERTA: Stock insuficiente para {product_ref.name}. Faltaron {qty_needed} unidades.")

            return Response({
                "message": "Orden creada exitosamente.", 
                "order_id": work_order.id,
                "order_folio": work_order.folio
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"ERROR: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
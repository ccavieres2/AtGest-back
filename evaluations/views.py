# evaluations/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction 

# 👇 IMPORTACIONES CRÍTICAS
from .models import Evaluation, EvaluationItem
from .serializers import EvaluationSerializer, EvaluationItemSerializer
from orders.models import WorkOrder  # 👈 Asegúrate de que esta línea esté
from accounts.utils import get_data_owner

class EvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return Evaluation.objects.filter(owner=target_user).order_by('-created_at')

    def perform_create(self, serializer):
        target_user = get_data_owner(self.request.user)
        vehicle = serializer.validated_data['vehicle']

        # Validación: Verificar si ya existe evaluación activa
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
        evaluation = self.get_object()
        items_data = request.data.get('items', [])
        
        EvaluationItem.objects.filter(evaluation=evaluation).delete()
        
        new_items = []
        for item in items_data:
            new_items.append(EvaluationItem(
                evaluation=evaluation,
                description=item.get('description'),
                price=item.get('price', 0),
                is_approved=item.get('is_approved', True)
            ))
        
        EvaluationItem.objects.bulk_create(new_items)
        return Response({'status': 'items updated'})

    # 👇 LA ACCIÓN GENERATE_ORDER DEBE ESTAR AL MISMO NIVEL DE INDENTACIÓN (TABULACIÓN)
    @action(detail=True, methods=['post'])
    def generate_order(self, request, pk=None):
        evaluation = self.get_object()

        # 1. Validar si ya existe
        if hasattr(evaluation, 'work_order'):
            return Response(
                {"error": "Ya existe una Orden de Trabajo para esta evaluación."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validar que tenga items aprobados
        # (Opcional: puedes quitar esto si quieres permitir órdenes vacías)
        approved_items = evaluation.items.filter(is_approved=True)
        if not approved_items.exists():
            return Response(
                {"error": "La evaluación no tiene ítems aprobados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Crear la Orden
        try:
            with transaction.atomic():
                evaluation.status = 'approved'
                evaluation.save()

                work_order = WorkOrder.objects.create(
                    evaluation=evaluation,
                    owner=evaluation.owner,
                    status='pending',
                    internal_notes=f"Generada desde Evaluación #{evaluation.id}"
                )

            return Response(
                {"message": "Orden creada", "order_id": work_order.id}, 
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Esto nos dirá en la consola exactamente qué pasó si falla
            print(f"ERROR GENERANDO ORDEN: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# evaluations/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError # 👈 Importar esto
from .models import Evaluation, EvaluationItem
from .serializers import EvaluationSerializer, EvaluationItemSerializer
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

        # 👇 VALIDACIÓN: Verificar si ya existe evaluación activa para este auto
        # Consideramos "activa" cualquier estado excepto 'rejected' (o los que tú definas como finalizados)
        active_statuses = ['draft', 'sent', 'approved'] 
        
        exists = Evaluation.objects.filter(
            vehicle=vehicle, 
            status__in=active_statuses
        ).exists()

        if exists:
            raise ValidationError({"vehicle": "Este vehículo ya tiene una evaluación en curso."})
        # 👆 FIN VALIDACIÓN

        serializer.save(owner=target_user)

    # ... (El resto del archivo, método update_items, sigue igual) ...
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
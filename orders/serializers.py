from rest_framework import serializers
from .models import WorkOrder
from evaluations.serializers import EvaluationSerializer

class WorkOrderSerializer(serializers.ModelSerializer):
    # Incluimos la evaluación completa para ver los detalles del auto y cliente
    evaluation_data = EvaluationSerializer(source='evaluation', read_only=True)
    
    mechanic_name = serializers.CharField(source='mechanic.username', read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'folio', 'evaluation', 'evaluation_data', 'owner', 
            'mechanic', 'mechanic_name', 'status', 
            'start_date', 'end_date', 'internal_notes', 
            'created_at'
        ]
        read_only_fields = ['owner', 'created_at']
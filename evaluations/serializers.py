# evaluations/serializers.py
from rest_framework import serializers
from .models import Evaluation, EvaluationItem
from clients.serializers import ClientSerializer, VehicleSerializer

class EvaluationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationItem
        # 👇 AGREGAMOS 'external_service_source' AQUÍ
        fields = ['id', 'description', 'price', 'is_approved', 'external_service_source']

class EvaluationSerializer(serializers.ModelSerializer):
    client_data = ClientSerializer(source='client', read_only=True)
    vehicle_data = VehicleSerializer(source='vehicle', read_only=True)
    items = EvaluationItemSerializer(many=True, read_only=True)
    
    # 👇 NUEVO CAMPO: Nombre del creador
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default="Sistema")

    class Meta:
        model = Evaluation
        fields = [
            'id', 'status', 'notes', 'created_at', 
            'client', 'vehicle',
            'client_data', 'vehicle_data',
            'items', 
            'created_by_name' # 👈 No olvides agregarlo aquí
        ]
        read_only_fields = ['owner', 'created_at', 'created_by']
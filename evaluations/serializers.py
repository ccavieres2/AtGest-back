# evaluations/serializers.py
from rest_framework import serializers
from .models import Evaluation, EvaluationItem
from clients.serializers import ClientSerializer, VehicleSerializer

class EvaluationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationItem
        # 👇 AGREGAMOS 'inventory_item' y 'quantity' AQUÍ
        fields = [
            'id', 
            'description', 
            'price', 
            'is_approved', 
            'external_service_source',
            'inventory_item',  # 👈 Campo Nuevo
            'quantity'         # 👈 Campo Nuevo
        ]

class EvaluationSerializer(serializers.ModelSerializer):
    client_data = ClientSerializer(source='client', read_only=True)
    vehicle_data = VehicleSerializer(source='vehicle', read_only=True)
    items = EvaluationItemSerializer(many=True, read_only=True)
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default="Sistema")

    class Meta:
        model = Evaluation
        fields = [
            'id', 'status', 'notes', 'created_at', 
            'client', 'vehicle',
            'client_data', 'vehicle_data',
            'items', 
            'created_by_name'
        ]
        read_only_fields = ['owner', 'created_at', 'created_by']
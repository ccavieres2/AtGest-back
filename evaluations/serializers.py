# evaluations/serializers.py
from rest_framework import serializers
from .models import Evaluation, EvaluationItem
from clients.serializers import ClientSerializer, VehicleSerializer # Para mostrar datos bonitos

class EvaluationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationItem
        fields = ['id', 'description', 'price', 'is_approved']

class EvaluationSerializer(serializers.ModelSerializer):
    # Nested serializers para lectura (ver datos completos)
    client_data = ClientSerializer(source='client', read_only=True)
    vehicle_data = VehicleSerializer(source='vehicle', read_only=True)
    
    # Items del checklist
    items = EvaluationItemSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluation
        fields = [
            'id', 'status', 'notes', 'created_at', 
            'client', 'vehicle', # IDs para escribir
            'client_data', 'vehicle_data', # Objetos para leer
            'items'
        ]
        read_only_fields = ['owner', 'created_at']
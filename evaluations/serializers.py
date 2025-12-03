# evaluations/serializers.py
from rest_framework import serializers
from .models import Evaluation, EvaluationItem
from clients.serializers import ClientSerializer, VehicleSerializer

class EvaluationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationItem
        fields = [
            'id', 'description', 'price', 'is_approved', 
            'external_service_source', 'inventory_item', 'quantity'
        ]

class EvaluationSerializer(serializers.ModelSerializer):
    client_data = ClientSerializer(source='client', read_only=True)
    vehicle_data = VehicleSerializer(source='vehicle', read_only=True)
    items = EvaluationItemSerializer(many=True, read_only=True)
    
    # 👇 CAMBIO: Usamos SerializerMethodField para evitar errores si created_by es None
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Evaluation
        fields = [
            'id', 'folio', 'status', 'notes', 'created_at', 
            'client', 'vehicle',
            'client_data', 'vehicle_data',
            'items', 'created_by_name'
        ]
        read_only_fields = ['owner', 'created_at', 'created_by', 'folio']

    # 👇 Método seguro: Si no hay creador, devuelve "Sistema" o "Desconocido"
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return "Sistema"
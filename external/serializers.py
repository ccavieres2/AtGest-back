# external/serializers.py
from rest_framework import serializers
from .models import ExternalService, ServiceRequest

class ExternalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalService
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')

# 👇 Serializer para las solicitudes B2B
class ServiceRequestSerializer(serializers.ModelSerializer):
    # Campos de lectura para mostrar nombres (útil para el frontend)
    service_name = serializers.CharField(source='service.name', read_only=True)
    requester_name = serializers.CharField(source='requester.username', read_only=True)
    provider_name = serializers.CharField(source='provider.username', read_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 
            'requester', 'requester_name', 
            'provider', 'provider_name', 
            'service', 'service_name', 
            'status', 
            'created_at', 
            'related_order_id'
        ]
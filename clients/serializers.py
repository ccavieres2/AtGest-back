# clients/serializers.py
from rest_framework import serializers
from .models import Client, Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'client', 'brand', 'model', 'year', 'plate', 'color', 'vin', 'created_at']

class ClientSerializer(serializers.ModelSerializer):
    # Incluimos los vehículos en modo lectura para verlos fácil al cargar el cliente
    vehicles = VehicleSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'first_name', 'last_name', 'rut', 'email', 'phone', 'address', 'vehicles', 'created_at']
        read_only_fields = ['owner', 'created_at']
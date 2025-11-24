# inventory/serializers.py
from rest_framework import serializers
from .models import InventoryItem

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = [
            "id", "name", "sku", "quantity", "price",
            "category", "location", "status",
            "created_at", "updated_at",
        ]
        # Agregamos 'owner' a read_only para que no se pida en el formulario
        read_only_fields = ("id", "created_at", "updated_at", "owner")

    # 👇 ELIMINAMOS el método 'create' personalizado. 
    # Dejamos que la vista (InventoryItemViewSet.perform_create) se encargue del dueño.
    
    def update(self, instance, validated_data):
        # Evita que cambien el owner manualmente
        validated_data.pop("owner", None)
        return super().update(instance, validated_data)
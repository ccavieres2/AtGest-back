# core/serializers.py
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
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        # Asigna automáticamente el usuario autenticado
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Evita que cambien el owner manualmente
        validated_data.pop("owner", None)
        return super().update(instance, validated_data)

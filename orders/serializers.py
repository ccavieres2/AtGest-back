# atgest-back/orders/serializers.py
from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Order
        # Usamos "__all__" para incluir automáticamente todos los campos del modelo
        fields = "__all__"
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
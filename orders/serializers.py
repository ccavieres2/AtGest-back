# atgest-back/orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem # 👈 1. Importar OrderItem
from inventory.serializers import InventoryItemSerializer # 👈 2. Importar Serializer de Inventario


# --- ⭐️ NUEVO: Serializer para el modelo intermedio ⭐️ ---
class OrderItemSerializer(serializers.ModelSerializer):
    # Anidamos una versión "lite" del item para saber qué producto es
    item = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "item", "quantity", "price_at_time_of_sale"]
    
    def get_item(self, obj):
        # Devuelve solo nombre, sku y id del producto
        if obj.item:
            return {
                "id": obj.item.id,
                "name": obj.item.name,
                "sku": obj.item.sku
            }
        return None
# --- -------------------------------------------- ---


class OrderSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    
    # 👈 3. Añadimos el serializer anidado
    # 'order_items' es el 'related_name' que definimos en el modelo OrderItem
    order_items = OrderItemSerializer(many=True, read_only=True)
    
    # 👈 4. Añadimos el costo total calculado
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = Order
        # Usamos "__all__" para incluir automáticamente los nuevos campos
        fields = "__all__"
        read_only_fields = ["id", "owner", "created_at", "updated_at", "order_items", "total_cost"]
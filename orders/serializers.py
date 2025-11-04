# atgest-back/orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem, ExternalServiceBooking # 👈 1. Importar ExternalServiceBooking
from inventory.serializers import InventoryItemSerializer 
from externalService.models import ExternalService # 👈 2. Importar ExternalService


# Serializer para el modelo intermedio (Inventario)
class OrderItemSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "item", "quantity", "price_at_time_of_sale"]
    
    def get_item(self, obj):
        if obj.item:
            return {
                "id": obj.item.id,
                "name": obj.item.name,
                "sku": obj.item.sku
            }
        return None

# --- 👈 3. NUEVO: Serializer para el modelo intermedio (Servicios Externos) ---
class ExternalServiceBookingSerializer(serializers.ModelSerializer):
    # Anidamos una versión "lite" del servicio para saber qué es
    service = serializers.SerializerMethodField()
    
    class Meta:
        model = ExternalServiceBooking
        fields = [
            'id', 
            'service', 
            'title_at_booking', 
            'price_at_booking', 
            'start_time', 
            'end_time',
            'created_at'
        ]
        read_only_fields = ['id', 'service', 'title_at_booking', 'price_at_booking', 'created_at']

    def get_service(self, obj):
        if obj.service:
            return {
                "id": obj.service.id,
                "title": obj.service.title,
                "owner": obj.service.owner.username
            }
        return None
# --- ----------------------------------------------------------------- ---


class OrderSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    
    # 'order_items' es el 'related_name' que definimos en el modelo OrderItem
    order_items = OrderItemSerializer(many=True, read_only=True)
    
    # 👈 4. AÑADIDO: 'service_bookings_through' es el 'related_name' del nuevo modelo
    service_bookings = ExternalServiceBookingSerializer(
        source='service_bookings_through', 
        many=True, 
        read_only=True
    )
    
    # 'total_cost' es la propiedad que actualizamos en models.py
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = [
            "id", "owner", "created_at", "updated_at", 
            "order_items", "total_cost", "service_bookings" # 👈 5. Añadir 'service_bookings'
        ]
# atgest-back/orders/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action 
from rest_framework.response import Response 
from .models import Order, OrderItem, ExternalServiceBooking # 👈 1. Importar ExternalServiceBooking
from inventory.models import InventoryItem  
from externalService.models import ExternalService # 👈 2. Importar ExternalService
from .serializers import OrderSerializer, OrderItemSerializer, ExternalServiceBookingSerializer # 👈 3. Importar Serializers
from django.shortcuts import get_object_or_404
from django.db import transaction 

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Order):
            return obj.owner == request.user
        if isinstance(obj, OrderItem):
            return obj.order.owner == request.user
        # 👈 4. AÑADIDO: Permiso para el nuevo modelo
        if isinstance(obj, ExternalServiceBooking):
            return obj.order.owner == request.user
        return False

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # 👈 5. MODIFICADO: prefetch_related optimiza AMBAS relaciones
        return Order.objects.filter(owner=self.request.user).prefetch_related(
            'order_items', 'order_items__item', 
            'service_bookings_through', 'service_bookings_through__service'
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    
    # --- Endpoint para añadir item a la orden ---
    @action(detail=True, methods=['post'], url_path='add-item')
    @transaction.atomic 
    def add_item(self, request, pk=None):
        order = self.get_object() 
        
        # 1. Obtener datos del request
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        if not item_id or quantity <= 0:
            return Response({"error": "Se requiere 'item_id' y 'quantity' positiva."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Obtener el producto del inventario (asegurándonos que es del usuario)
        item = get_object_or_404(InventoryItem, pk=item_id, owner=request.user)
        
        # 3. Verificar Stock
        if item.quantity < quantity:
            return Response({"error": f"Stock insuficiente para '{item.name}'. Disponible: {item.quantity}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 4. Verificar estado de la orden (¡NUEVO!)
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_AWAITING_APPROVAL]:
            return Response({"error": "Solo se pueden agregar ítems a órdenes pendientes o esperando aprobación."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 5. Restar Stock
        item.quantity -= quantity
        item.save()
        
        # 6. Crear o actualizar el OrderItem
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            item=item,
            defaults={'price_at_time_of_sale': item.price, 'quantity': quantity}
        )
        
        if not created:
            order_item.quantity += quantity
            order_item.save()

        # 7. Responder con la orden completa
        # (El costo total se recalcula automáticamente por la propiedad del modelo)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
    # --- 👈 6. NUEVO: Endpoint para añadir servicio externo a la orden ⭐️ ---
    @action(detail=True, methods=['post'], url_path='add-service')
    @transaction.atomic
    def add_service(self, request, pk=None):
        order = self.get_object() # Obtiene la orden (ej: /orders/10/...)
        
        # 1. Obtener datos del request
        service_id = request.data.get('service_id')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if not service_id or not start_time or not end_time:
            return Response({"error": "Se requiere 'service_id', 'start_time' y 'end_time'"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Obtener el servicio externo
        service = get_object_or_404(ExternalService, pk=service_id)

        # 3. Verificar estado de la orden
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_AWAITING_APPROVAL]:
            return Response({"error": "Solo se pueden agregar servicios a órdenes pendientes o esperando aprobación."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. (Opcional) Validar que el horario sea válido
        # ... (Aquí podrías añadir lógica para verificar que el start/end time
        # ... realmente existe en service.available_hours y no está ocupado)
        
        # 5. Crear la reserva (Booking)
        try:
            booking = ExternalServiceBooking.objects.create(
                order=order,
                service=service,
                title_at_booking=service.title,
                price_at_booking=service.price,
                start_time=start_time, # Django parseará el string ISO
                end_time=end_time
            )
        except Exception as e:
            # Captura error si, por ejemplo, 'unique_together' falla
            return Response({"error": f"No se pudo agendar la reserva. ¿Quizás ya existe? ({str(e)})"}, status=status.HTTP_400_BAD_REQUEST)

        # 6. Responder con la orden actualizada
        # (El costo total se recalcula automáticamente por la propiedad del modelo)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # --- ----------------------------------------------------------------- ---
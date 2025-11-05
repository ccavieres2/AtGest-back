# ccavieres2/atgest-back/AtGest-back-824796a5f5f0a1747c754d4ec544338810379597/orders/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action 
from rest_framework.response import Response 
from .models import Order, OrderItem, ExternalServiceBooking
from inventory.models import InventoryItem  
from externalService.models import ExternalService 
from .serializers import OrderSerializer, OrderItemSerializer, ExternalServiceBookingSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction 
from dateutil.parser import isoparse # 👈 1. IMPORTAR ISOPARSE

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Order):
            return obj.owner == request.user
        if isinstance(obj, OrderItem):
            return obj.order.owner == request.user
        if isinstance(obj, ExternalServiceBooking):
            return obj.order.owner == request.user
        return False

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user).prefetch_related(
            'order_items', 'order_items__item', 
            'service_bookings_through', 'service_bookings_through__service'
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    
    # --- Endpoint para añadir item a la orden (Sin cambios) ---
    @action(detail=True, methods=['post'], url_path='add-item')
    @transaction.atomic 
    def add_item(self, request, pk=None):
        order = self.get_object() 
        
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        if not item_id or quantity <= 0:
            return Response({"error": "Se requiere 'item_id' y 'quantity' positiva."}, status=status.HTTP_400_BAD_REQUEST)

        item = get_object_or_404(InventoryItem, pk=item_id, owner=request.user)
        
        if item.quantity < quantity:
            return Response({"error": f"Stock insuficiente para '{item.name}'. Disponible: {item.quantity}"}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_AWAITING_APPROVAL]:
            return Response({"error": "Solo se pueden agregar ítems a órdenes pendientes o esperando aprobación."}, status=status.HTTP_400_BAD_REQUEST)
            
        item.quantity -= quantity
        item.save()
        
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            item=item,
            defaults={'price_at_time_of_sale': item.price, 'quantity': quantity}
        )
        
        if not created:
            order_item.quantity += quantity
            order_item.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
    # --- 👈 2. Endpoint 'add-service' (ACTUALIZADO) ---
    @action(detail=True, methods=['post'], url_path='add-service')
    @transaction.atomic
    def add_service(self, request, pk=None):
        order = self.get_object() 
        
        # 1. Obtener datos del request
        service_id = request.data.get('service_id')
        start_time_str = request.data.get('start_time') # 👈 Recibir como string
        end_time_str = request.data.get('end_time')     # 👈 Recibir como string

        if not service_id or not start_time_str or not end_time_str:
            return Response({"error": "Se requiere 'service_id', 'start_time' y 'end_time'"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Obtener el servicio externo
        service = get_object_or_404(ExternalService, pk=service_id)

        # 3. Verificar estado de la orden
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_AWAITING_APPROVAL]:
            return Response({"error": "Solo se pueden agregar servicios a órdenes pendientes o esperando aprobación."}, status=status.HTTP_400_BAD_REQUEST)

        # --- ⭐️ 3. NUEVA LÓGICA DE VALIDACIÓN Y ACTUALIZACIÓN ⭐️ ---
        try:
            # 3.1. Convertir los strings de entrada a objetos datetime (con zona horaria)
            req_start_time = isoparse(start_time_str)
            req_end_time = isoparse(end_time_str)
        except ValueError:
            return Response({"error": "Formato de fecha inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # 3.2. Encontrar el slot en available_hours y filtrarlo
        found_slot = None
        updated_available_hours = []
        
        for slot in service.available_hours:
            try:
                # Convertir strings del JSON a objetos datetime (con zona horaria)
                slot_start_time = isoparse(slot['start'])
                slot_end_time = isoparse(slot['end'])

                # Comprobar si coincide EXACTAMENTE
                if slot_start_time == req_start_time and slot_end_time == req_end_time:
                    found_slot = slot # Encontramos el slot a reservar
                else:
                    updated_available_hours.append(slot) # Mantener los que no coinciden
            except (KeyError, ValueError):
                # Ignorar slots mal formados en el JSON
                continue

        # 3.3. Si no se encontró el slot, es un error
        if not found_slot:
            return Response({"error": "El horario seleccionado ya no está disponible o no existe."}, status=status.HTTP_409_CONFLICT) # 409 Conflict

        # 3.4. Si se encontró, actualizar el JSON del servicio y guardarlo
        service.available_hours = updated_available_hours
        service.save()
        
        # --- FIN DE LA NUEVA LÓGICA ---

        # 4. Crear la reserva (Booking)
        try:
            booking = ExternalServiceBooking.objects.create(
                order=order,
                service=service,
                title_at_booking=service.title, # Usar el título del servicio
                price_at_booking=service.price,
                start_time=req_start_time, # 👈 Usar el objeto datetime
                end_time=req_end_time      # 👈 Usar el objeto datetime
            )
        except Exception as e:
            # Si esto falla (ej. unique_together), la transacción
            # revertirá el service.save(), lo cual es perfecto.
            return Response({"error": f"No se pudo agendar la reserva. ¿Quizás ya existe? ({str(e)})"}, status=status.HTTP_400_BAD_REQUEST)

        # 5. Responder con la orden actualizada
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # --- ----------------------------------------------------------------- ---
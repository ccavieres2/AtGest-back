# atgest-back/orders/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action # 👈 1. Importar 'action'
from rest_framework.response import Response # 👈 1. Importar 'Response'
from .models import Order, OrderItem        # 👈 1. Importar OrderItem
from inventory.models import InventoryItem  # 👈 1. Importar InventoryItem
from .serializers import OrderSerializer, OrderItemSerializer # 👈 1. Importar OrderItemSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction # 👈 1. Importar 'transaction'

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Si el objeto es una Orden, comprueba el dueño
        if isinstance(obj, Order):
            return obj.owner == request.user
        # Si es un OrderItem, comprueba que seas dueño de la orden principal
        if isinstance(obj, OrderItem):
            return obj.order.owner == request.user
        return False

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Solo ver tus órdenes
        # 👈 2. 'prefetch_related' optimiza la consulta de items anidados
        return Order.objects.filter(owner=self.request.user).prefetch_related('order_items', 'order_items__item')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    
    # --- ⭐️ NUEVO: Endpoint para añadir item a la orden ⭐️ ---
    @action(detail=True, methods=['post'], url_path='add-item')
    @transaction.atomic # 👈 Si algo falla (ej: no hay stock), revierte toda la operación
    def add_item(self, request, pk=None):
        order = self.get_object() # Obtiene la orden (ej: /orders/10/...)
        
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
            
        # 4. Restar Stock
        item.quantity -= quantity
        item.save()
        
        # 5. Crear o actualizar el OrderItem
        # Usamos get_or_create por si el item ya estaba en la orden
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            item=item,
            # Si se crea, se usa este precio. Si ya existía, no se actualiza.
            defaults={'price_at_time_of_sale': item.price, 'quantity': quantity}
        )
        
        # Si no fue creado (ya existía), actualizamos la cantidad
        if not created:
            order_item.quantity += quantity
            # Opcional: ¿actualizar el precio al más nuevo? Decidamos que no.
            # order_item.price_at_time_of_sale = item.price 
            order_item.save()

        # 6. Responder con el item creado/actualizado
        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # --- ----------------------------------------------- ---
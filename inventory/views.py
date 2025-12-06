# inventory/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Product, InventoryBatch
from .serializers import ProductSerializer, InventoryBatchSerializer
from accounts.utils import get_data_owner

# --- VIEWSET 1: GESTIÓN DE PRODUCTOS (CATÁLOGO) ---
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return Product.objects.filter(owner=target_user).order_by('name')

    def perform_create(self, serializer):
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)

    # Endpoint extra para ver los lotes de un producto específico
    # GET /api/inventory/products/{id}/batches/
    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        product = self.get_object()
        # Solo mostramos lotes que aún tengan stock
        batches = product.batches.filter(current_quantity__gt=0).order_by('expiration_date')
        serializer = InventoryBatchSerializer(batches, many=True)
        return Response(serializer.data)


# --- VIEWSET 2: GESTIÓN DE LOTES (ENTRADAS DE MERCADERÍA) ---
class InventoryBatchViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        # Filtramos lotes de productos que pertenezcan al usuario
        return InventoryBatch.objects.filter(product__owner=target_user).order_by('-entry_date')

    def create(self, request, *args, **kwargs):
        # Copiamos los datos para manipularlos
        data = request.data.copy()
        
        # Si no envían 'current_quantity', asumimos que es igual a 'initial_quantity' (producto nuevo)
        if 'initial_quantity' in data and 'current_quantity' not in data:
            data['current_quantity'] = data['initial_quantity']
            
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Seguridad: Validar que el producto al que le agregan stock sea del usuario
        product = serializer.validated_data['product']
        target_user = get_data_owner(request.user)
        
        if product.owner != target_user:
             return Response({"error": "No tienes permiso para agregar stock a este producto."}, status=403)

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
# inventory/serializers.py
from rest_framework import serializers
from .models import Product, InventoryBatch

class InventoryBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = [
            'id', 'product', 'initial_quantity', 'current_quantity', 
            'unit_cost', 'entry_date', 'expiration_date', 'created_at'
        ]
        # Permitimos editar TODO menos la fecha de creación
        read_only_fields = ['created_at']

class ProductSerializer(serializers.ModelSerializer):
    stock_actual = serializers.IntegerField(source='total_stock', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 
            'category', 'location', 'sale_price', 
            'stock_actual', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
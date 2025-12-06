# inventory/admin.py
from django.contrib import admin
from .models import Product, InventoryBatch

class InventoryBatchInline(admin.TabularInline):
    model = InventoryBatch
    extra = 0
    readonly_fields = ('current_quantity', 'created_at')
    can_delete = False

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "total_stock", "category", "owner")
    search_fields = ("name", "sku", "owner__username")
    list_filter = ("category",)
    inlines = [InventoryBatchInline] # Permite ver los lotes dentro del producto

    # Mostramos el stock total calculado
    def total_stock(self, obj):
        return obj.total_stock
    total_stock.short_description = "Stock Total"

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ("product", "initial_quantity", "current_quantity", "entry_date", "expiration_date")
    list_filter = ("entry_date", "expiration_date")
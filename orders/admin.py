# atgest-back/orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem # 👈 1. Importar OrderItem

# ⭐️ NUEVO: Un 'inline' para ver/agregar productos dentro de la página de la Orden ⭐️
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1 # Cuántos campos vacíos mostrar
    autocomplete_fields = ['item'] # Asume que tienes búsqueda en el admin de inventario

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "client_name",
        "vehicle_plate",
        "vehicle_model", 
        "service_title",
        "status", 
        "owner", 
        "created_at"
    )
    list_filter = ("status", "owner")
    search_fields = (
        "client_name", 
        "client_phone", 
        "vehicle_plate", 
        "vehicle_model", 
        "vehicle_vin",
        "service_title"
    )
    inlines = [OrderItemInline] # 👈 2. Añadir el inline aquí
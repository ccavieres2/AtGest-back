# atgest-back/orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem, ExternalServiceBooking # 👈 1. Importar ExternalServiceBooking

# Inline para Items de Inventario
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 # Cambiado a 0 para no saturar
    autocomplete_fields = ['item'] 

# 👈 2. NUEVO: Inline para Servicios Externos
class ExternalServiceBookingInline(admin.TabularInline):
    model = ExternalServiceBooking
    extra = 0 # Cuántos campos vacíos mostrar
    autocomplete_fields = ['service'] # Asume que tienes búsqueda en el admin de ExternalService
    readonly_fields = ['title_at_booking', 'price_at_booking'] # Estos se llenan solos

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
    # 👈 3. Añadir el nuevo inline aquí
    inlines = [OrderItemInline, ExternalServiceBookingInline]
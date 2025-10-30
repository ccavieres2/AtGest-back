from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # 👇 Hemos actualizado los campos a los nuevos nombres del modelo
    list_display = (
        "id", 
        "client_name",        # <- "client" ahora es "client_name"
        "vehicle_plate",      # <- "vehicle" ahora es "vehicle_plate"
        "vehicle_model", 
        "service_title",      # <- "service" ahora es "service_title"
        "status", 
        "owner", 
        "created_at"
    )
    
    list_filter = ("status", "owner")
    
    # 👇 También actualizamos los campos de búsqueda
    search_fields = (
        "client_name", 
        "client_phone", 
        "vehicle_plate", 
        "vehicle_model", 
        "vehicle_vin",
        "service_title"
    )
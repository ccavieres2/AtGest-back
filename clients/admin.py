from django.contrib import admin

# clients/admin.py
from django.contrib import admin
from .models import Client, Vehicle

# Esta clase permite editar los vehículos DENTRO de la pantalla del cliente
class VehicleInline(admin.StackedInline):
    model = Vehicle
    extra = 0  # No mostrar formularios vacíos extra por defecto

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Columnas que se verán en la lista
    list_display = ('first_name', 'last_name', 'rut', 'email', 'phone', 'owner', 'created_at')
    
    # Campos por los que se podrá buscar
    search_fields = ('first_name', 'last_name', 'rut', 'email', 'owner__username')
    
    # Filtros laterales
    list_filter = ('owner', 'created_at')
    
    # Agregamos los vehículos para editarlos en la misma página del cliente
    inlines = [VehicleInline]

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'plate', 'year', 'client', 'created_at')
    search_fields = ('brand', 'model', 'plate', 'vin', 'client__first_name', 'client__last_name', 'client__rut')
    list_filter = ('brand', 'year', 'client__owner') # Filtrar por marca, año o por el dueño del taller
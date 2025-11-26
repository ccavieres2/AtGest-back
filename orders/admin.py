from django.contrib import admin
from .models import WorkOrder

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle_plate', 'client_name', 'mechanic', 'status', 'created_at')
    list_filter = ('status', 'mechanic', 'created_at', 'owner')
    search_fields = ('evaluation__vehicle__plate', 'evaluation__client__first_name', 'evaluation__client__last_name', 'internal_notes')
    autocomplete_fields = ['evaluation', 'mechanic'] # Útil si tienes muchos registros
    
    # Métodos para acceder a datos relacionados (ya que evaluation es ForeignKey)
    def vehicle_plate(self, obj):
        return obj.evaluation.vehicle.plate
    vehicle_plate.short_description = "Patente"

    def client_name(self, obj):
        return f"{obj.evaluation.client.first_name} {obj.evaluation.client.last_name}"
    client_name.short_description = "Cliente"
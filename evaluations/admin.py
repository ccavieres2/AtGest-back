from django.contrib import admin
from .models import Evaluation, EvaluationItem

class EvaluationItemInline(admin.TabularInline):
    model = EvaluationItem
    extra = 0 # No muestra filas vacías extra
    fields = ('description', 'price', 'is_approved')

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'vehicle', 'status', 'total_price', 'owner', 'created_at')
    list_filter = ('status', 'created_at', 'owner')
    search_fields = ('client__first_name', 'client__last_name', 'vehicle__plate', 'id')
    inlines = [EvaluationItemInline]
    
    # Método auxiliar para mostrar el total en la lista
    def total_price(self, obj):
        total = sum(item.price for item in obj.items.all())
        return f"${total:,.0f}"
    total_price.short_description = "Total Estimado"

@admin.register(EvaluationItem)
class EvaluationItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'evaluation', 'price', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('description', 'evaluation__client__first_name')
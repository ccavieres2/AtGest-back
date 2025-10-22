# core/admin.py
from django.contrib import admin
from .models import InventoryItem

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "quantity", "price", "status", "category", "owner")
    search_fields = ("name", "sku", "category", "owner__username")
    list_filter = ("status", "category")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

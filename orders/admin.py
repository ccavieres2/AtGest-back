from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "vehicle", "service", "status", "owner", "created_at")
    list_filter = ("status", "owner")
    search_fields = ("client", "vehicle", "service")

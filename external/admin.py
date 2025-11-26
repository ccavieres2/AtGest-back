from django.contrib import admin
from .models import ExternalService

@admin.register(ExternalService)
class ExternalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_name', 'category', 'cost', 'phone', 'owner', 'created_at')
    list_filter = ('category', 'created_at', 'owner')
    search_fields = ('name', 'provider_name', 'description', 'phone')
    ordering = ('-created_at',)
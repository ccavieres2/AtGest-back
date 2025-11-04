# atgest-back/externalService/admin.py
from django.contrib import admin
from .models import ExternalService

@admin.register(ExternalService)
class ExternalServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'price', 'available', 'created_at')
    list_filter = ('available', 'owner', 'category')
    
    # --- 1. AÑADE ESTA LÍNEA ---
    search_fields = ('title', 'description', 'owner__username', 'category')
    # --- -------------------- ---
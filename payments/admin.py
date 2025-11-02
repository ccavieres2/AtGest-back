# atgest-back/payments/admin.py
from django.contrib import admin
from .models import UserPayment # 👈 Importa el nuevo modelo

# (Puedes borrar el "Register your models here.")

@admin.register(UserPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'paypal_order_id', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('user__username', 'paypal_order_id')
# atgest-back/payments/models.py
from django.db import models
from django.conf import settings

# (Puedes borrar el "Create your models here.")

class UserPayment(models.Model):
    # Vincula el pago a un usuario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # No borrar el pago si se borra el usuario
        null=True, 
        blank=True, 
        related_name="payments"
    )
    # El ID de la transacción que nos da PayPal
    paypal_order_id = models.CharField(max_length=100, unique=True)
    
    # Detalles del pago
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=50) # ej: "COMPLETED"
    
    # Cuándo se hizo
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.username if self.user else "Usuario no asignado"
        return f"{username} - {self.paypal_order_id} ({self.status})"
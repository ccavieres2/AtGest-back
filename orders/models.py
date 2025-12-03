# orders/models.py
from django.db import models
from django.conf import settings
from evaluations.models import Evaluation

class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Reparación'),
        ('waiting_parts', 'Esperando Repuestos'),
        ('finished', 'Terminado'),
        ('delivered', 'Entregado'),
    ]
    evaluation = models.OneToOneField(Evaluation, on_delete=models.CASCADE, related_name='work_order')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="work_orders")
    mechanic = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_orders")
    
    # 👇 ESTE CAMPO ES CLAVE PARA COMPARTIR EL NÚMERO
    folio = models.PositiveIntegerField(null=True, blank=True, verbose_name="Folio")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    last_status_change_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="status_changes"
    )
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    internal_notes = models.TextField(blank=True, verbose_name="Notas para mecánico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Usamos el Folio para la representación en texto
        return f"OT #{self.folio} - {self.evaluation.vehicle}"
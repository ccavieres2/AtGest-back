# evaluations/models.py
from django.db import models
from django.conf import settings
from clients.models import Client, Vehicle
from external.models import ExternalService # 👈 Importante: Importamos el modelo externo

class Evaluation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviado al Cliente'),
        ('approved', 'Aprobado (Parcial o Total)'),
        ('rejected', 'Rechazado'),
    ]

    # Relaciones
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # El taller
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="evaluations")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="evaluations")
    
    # Datos
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, verbose_name="Observaciones generales")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Eval #{self.id} - {self.vehicle}"

class EvaluationItem(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255, verbose_name="Descripción del problema/repuesto")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo estimado")
    
    # El "Check": si el cliente aprueba este ítem para reparación
    is_approved = models.BooleanField(default=True, verbose_name="Aprobado por cliente")
    
    # 👇 NUEVO CAMPO: Vincula este ítem a un servicio del mercado
    external_service_source = models.ForeignKey(
        ExternalService, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="linked_items"
    )

    def __str__(self):
        return self.description
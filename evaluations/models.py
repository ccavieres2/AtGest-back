# evaluations/models.py
from django.db import models
from django.conf import settings
from django.db.models import Max  # Se mantiene por si necesitas Max en otro lado, aunque ya no es crítico para el folio
from clients.models import Client, Vehicle
from external.models import ExternalService
from inventory.models import InventoryItem

class Evaluation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviado al Cliente'),
        ('approved', 'Aprobado (Parcial o Total)'),
        ('rejected', 'Rechazado'),
    ]

    # Relaciones
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Quién creó el registro (Empleado o Dueño)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_evaluations"
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="evaluations")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="evaluations")
    
    # Datos
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Folio único por taller (editable=False para que no se toque en admin directamente)
    folio = models.PositiveIntegerField(editable=False, null=True, blank=True, verbose_name="Folio")
    
    notes = models.TextField(blank=True, verbose_name="Observaciones generales")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 👇 LÓGICA DE FOLIOS MEJORADA (RELLENO DE HUECOS)
    def save(self, *args, **kwargs):
        # Solo calculamos si no tiene folio asignado (es nuevo)
        if not self.folio:
            # 1. Obtenemos todos los folios existentes de este dueño, ordenados de menor a mayor
            # values_list devuelve solo los números: [1, 2, 4, 5...]
            existing_folios = Evaluation.objects.filter(owner=self.owner).values_list('folio', flat=True).order_by('folio')
            
            # 2. Algoritmo para encontrar el primer número libre
            next_folio = 1
            for folio in existing_folios:
                if folio == next_folio:
                    # Si el número existe en la BD, pasamos al siguiente esperado
                    next_folio += 1
                else:
                    # Si el número en la BD es mayor al esperado (ej: esperamos 3 pero viene 4),
                    # significa que el 3 está libre. Rompemos el ciclo y usamos next_folio (3).
                    break
            
            # Asignamos el número encontrado (sea un hueco intermedio o el siguiente al final)
            self.folio = next_folio
            
        super().save(*args, **kwargs)

    def __str__(self):
        # Mostramos el Folio en lugar del ID para consistencia visual
        return f"Eval #{self.folio} - {self.vehicle}"

class EvaluationItem(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255, verbose_name="Descripción del problema/repuesto")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo estimado")
    
    # Si el cliente aprueba este ítem
    is_approved = models.BooleanField(default=True, verbose_name="Aprobado por cliente")
    
    # Vinculación con servicio externo (Integración External)
    external_service_source = models.ForeignKey(
        ExternalService, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="linked_items"
    )

    # Vinculación con inventario (Integración Inventory)
    inventory_item = models.ForeignKey(
        InventoryItem, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="evaluation_items"
    )
    # Cantidad para descontar del stock o calcular precio
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    def __str__(self):
        return self.description
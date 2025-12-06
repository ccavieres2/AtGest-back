# evaluations/models.py
from django.db import models
from django.conf import settings
from clients.models import Client, Vehicle
from external.models import ExternalService
# 👇 CAMBIO: Importamos Product en lugar de InventoryItem
from inventory.models import Product 

class Evaluation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviado al Cliente'),
        ('approved', 'Aprobado (Parcial o Total)'),
        ('rejected', 'Rechazado'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="created_evaluations"
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="evaluations")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="evaluations")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    folio = models.PositiveIntegerField(editable=False, null=True, blank=True, verbose_name="Folio")
    notes = models.TextField(blank=True, verbose_name="Observaciones generales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.folio:
            existing_folios = Evaluation.objects.filter(owner=self.owner).values_list('folio', flat=True).order_by('folio')
            next_folio = 1
            for folio in existing_folios:
                if folio == next_folio:
                    next_folio += 1
                else:
                    break
            self.folio = next_folio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Eval #{self.folio} - {self.vehicle}"

class EvaluationItem(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255, verbose_name="Descripción")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo estimado")
    is_approved = models.BooleanField(default=True, verbose_name="Aprobado por cliente")
    
    external_service_source = models.ForeignKey(
        ExternalService, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="linked_items"
    )

    # 👇 CAMBIO: Ahora apunta a 'Product' (el catálogo)
    # Mantenemos el nombre 'inventory_item' para no romper todo el frontend de golpe,
    # pero internamente es un Producto.
    inventory_item = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="evaluation_items"
    )
    
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    def __str__(self):
        return self.description
# atgest-back/orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Order(models.Model):
    # (Recepción/Pendiente)
    STATUS_PENDING = "pending"
    # (Esperando aprobación de presupuesto por cliente)
    STATUS_AWAITING_APPROVAL = "awaiting_approval"
    # (En proceso en el taller)
    STATUS_IN_PROGRESS = "in_progress"
    # (Esperando repuestos)
    STATUS_AWAITING_PARTS = "awaiting_parts"
    # (Trabajo finalizado)
    STATUS_DONE = "done"
    # (Orden cancelada)
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_AWAITING_APPROVAL, "Esperando Aprobación"),
        (STATUS_IN_PROGRESS, "En Taller"),
        (STATUS_AWAITING_PARTS, "Esperando Repuestos"),
        (STATUS_DONE, "Completado"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    # --- Campos de la Orden ---
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # --- Información del Cliente ---
    client_name = models.CharField("Nombre Cliente", max_length=120)
    client_phone = models.CharField("Teléfono Cliente", max_length=20, blank=True)
    client_email = models.EmailField("Email Cliente", max_length=100, blank=True)

    # --- Información del Vehículo ---
    vehicle_plate = models.CharField("Patente", max_length=10, blank=True, null=True)
    vehicle_make = models.CharField("Marca", max_length=50, blank=True)
    vehicle_model = models.CharField("Modelo", max_length=50)
    vehicle_year = models.PositiveIntegerField("Año", null=True, blank=True)
    vehicle_vin = models.CharField("VIN (Chasis)", max_length=17, blank=True)

    # --- Información del Servicio ---
    service_title = models.CharField("Título del Servicio", max_length=160)
    service_description = models.TextField("Notas / Descripción del problema", blank=True)
    
    # --- Fechas ---
    scheduled_date = models.DateTimeField("Fecha Agendada", null=True, blank=True)
    completed_date = models.DateTimeField("Fecha Completado", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Costos ---
    estimated_cost = models.DecimalField("Costo Estimado", max_digits=10, decimal_places=2, default=0)
    final_cost = models.DecimalField("Costo Final", max_digits=10, decimal_places=2, null=True, blank=True)


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client_name} - {self.vehicle_model} ({self.get_status_display()})"
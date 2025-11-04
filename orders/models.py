# atgest-back/orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from inventory.models import InventoryItem
from externalService.models import ExternalService # 👈 1. Importar ExternalService

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
    # ❗️ NOTA: 'final_cost' ahora representa 'Mano de Obra / Costo del Servicio'
    estimated_cost = models.DecimalField("Costo Estimado", max_digits=10, decimal_places=2, default=0)
    final_cost = models.DecimalField("Costo Final (Mano de Obra)", max_digits=10, decimal_places=2, null=True, blank=True)

    # --- Relación con productos de inventario ---
    items = models.ManyToManyField(
        InventoryItem,
        through='OrderItem', # Usamos el modelo intermedio
        related_name='orders'
    )
    
    # --- 👈 2. NUEVA: Relación con servicios externos ---
    service_bookings = models.ManyToManyField(
        ExternalService,
        through='ExternalServiceBooking', # Usamos el nuevo modelo intermedio
        related_name='orders'
    )
    # --- -------------------------------------------- ---


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client_name} - {self.vehicle_model} ({self.get_status_display()})"
        
    # 👈 3. MODIFICADO: Propiedad para calcular el total
    @property
    def total_cost(self):
        # Suma el costo final (mano de obra)
        total = self.final_cost if self.final_cost else Decimal('0.0')
        
        # Suma el costo de todos los items
        items_cost = self.order_items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('price_at_time_of_sale'))
        )['total']
        
        if items_cost:
            total += items_cost
            
        # 👈 4. NUEVO: Sumar el costo de los servicios externos
        services_cost = self.service_bookings_through.aggregate(
            total=models.Sum('price_at_booking')
        )['total']
        
        if services_cost:
            total += services_cost
            
        return total


# --- Modelo Intermedio (Inventario) ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True, related_name="order_items")
    
    quantity = models.PositiveIntegerField(default=1)
    price_at_time_of_sale = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        item_name = self.item.name if self.item else "Producto eliminado"
        return f"{self.quantity} x {item_name} (en Orden #{self.order.id})"

    class Meta:
        unique_together = ('order', 'item')


# --- 👈 5. NUEVO: Modelo Intermedio (Servicios Externos) ---
class ExternalServiceBooking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="service_bookings_through")
    service = models.ForeignKey(ExternalService, on_delete=models.SET_NULL, null=True, related_name="bookings")
    
    # Guardamos "snapshots" de los datos al momento de la reserva
    title_at_booking = models.CharField(max_length=255)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2)
    
    # El horario que el usuario seleccionó
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        # Evitar que se agende el mismo servicio a la misma hora en la misma orden
        unique_together = ('order', 'service', 'start_time')

    def __str__(self):
        return f"Booking for '{self.title_at_booking}' in Order {self.order.id}"
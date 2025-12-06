## inventory/models.py
from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

# --- TABLA 1: PRODUCTO (El Catálogo - Qué es) ---
class Product(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=120, verbose_name="Nombre Producto")
    sku = models.CharField(max_length=64, verbose_name="Código SKU")
    description = models.TextField(blank=True, verbose_name="Descripción")
    category = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=80, blank=True, verbose_name="Ubicación")
    
    # Precio de venta al público (sugerido)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Venta")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Evita duplicar el mismo código SKU en el taller
        constraints = [
            models.UniqueConstraint(fields=["owner", "sku"], name="unique_product_sku_per_owner")
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    # Propiedad para obtener el stock total sumando los lotes
    @property
    def total_stock(self):
        # Suma la columna 'current_quantity' de todos los lotes asociados
        return self.batches.aggregate(total=Sum('current_quantity'))['total'] or 0


# --- TABLA 2: LOTE DE INVENTARIO (Las Existencias - Cuántos hay y cuándo vencen) ---
class InventoryBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    
    # Cantidad inicial que entró
    initial_quantity = models.PositiveIntegerField(verbose_name="Cantidad Entrada")
    
    # Cantidad que queda actualmente (se reduce con las salidas)
    current_quantity = models.PositiveIntegerField(verbose_name="Stock Actual")
    
    # Costo al que compraste este lote
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Costo Compra")
    
    # Fechas solicitadas por tu profesora
    entry_date = models.DateField(default=timezone.now, verbose_name="Fecha de Ingreso")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ordenar para que salgan primero los que vencen antes (FIFO)
        ordering = ['expiration_date', 'entry_date']

    def __str__(self):
        return f"Lote {self.id} - {self.product.name}"

    def save(self, *args, **kwargs):
        # Al crear, si no se especifica stock actual, es igual al inicial
        if self.current_quantity is None:
            self.current_quantity = self.initial_quantity
        super().save(*args, **kwargs)
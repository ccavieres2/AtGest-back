# core/models.py
from django.db import models
from django.conf import settings


class InventoryItem(models.Model):
    STATUS_CHOICES = [
        ("active", "Activo"),
        ("inactive", "Inactivo"),
        ("out", "Sin stock"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_items",
        null=True,  # 👈 agrega esto
        blank=True  # 👈 opcional, para el panel admin
    )


    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "sku"], name="unique_sku_per_owner")
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

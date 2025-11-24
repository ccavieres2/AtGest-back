# clients/models.py
from django.db import models
from django.conf import settings

class Client(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients"
    )
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    rut = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUT/DNI")
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# 👇 NUEVO MODELO
class Vehicle(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="vehicles")
    brand = models.CharField(max_length=50, verbose_name="Marca")     # Ej: Toyota
    model = models.CharField(max_length=50, verbose_name="Modelo")    # Ej: Yaris
    year = models.PositiveIntegerField(verbose_name="Año")            # Ej: 2018
    plate = models.CharField(max_length=10, verbose_name="Patente")   # Ej: HYKG-99
    color = models.CharField(max_length=30, blank=True, null=True)
    vin = models.CharField(max_length=50, blank=True, null=True, verbose_name="Chasis/VIN")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate})"
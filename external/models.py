from django.db import models
from django.conf import settings

class ExternalService(models.Model):
    CATEGORY_CHOICES = [
        ('mechanic', 'Mecánica Especializada'),
        ('lathe', 'Tornería / Rectificadora'),
        ('paint', 'Desabolladura y Pintura'),
        ('electric', 'Electricidad'),
        ('other', 'Otros'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="external_services"
    )
    name = models.CharField(max_length=150, verbose_name="Nombre del Servicio")
    provider_name = models.CharField(max_length=150, verbose_name="Nombre Proveedor/Taller")
    description = models.TextField(blank=True, verbose_name="Descripción")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Estimado")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono contacto")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.provider_name}"
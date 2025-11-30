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
    
# 👇 NUEVO MODELO PARA LAS SOLICITUDES
class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('completed', 'Completada'),
    ]

    # Quien pide el servicio (Iván)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_requests")
    
    # Quien provee el servicio (Carlos - Dueño del servicio)
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_requests")
    
    # El servicio original
    service = models.ForeignKey(ExternalService, on_delete=models.CASCADE)
    
    # Detalles
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Opcional: Vincular a la OT de Iván para referencia
    related_order_id = models.IntegerField(null=True, blank=True, help_text="ID de la WorkOrder de origen")

    def __str__(self):
        return f"Request {self.id} from {self.requester} to {self.provider}"
# models.py
from django.db import models
from django.contrib.auth.models import User

class ExternalService(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="external_services")
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(help_text="Duración estimada en minutos", null=True, blank=True)
    available_hours = models.JSONField(default=list, blank=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="external_services/", null=True, blank=True)
    
    def __str__(self):
        return self.title
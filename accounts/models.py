# accounts/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLES = (
        ('owner', 'Dueño'),
        ('mechanic', 'Mecánico'),
        ('assistant', 'Ayudante'),
        ('admin', 'Administración'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLES, default='owner')
    
    # 👇 NUEVO CAMPO
    phone = models.CharField(max_length=20)
    
    employer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Opcional: Para saber a dónde redirigir al dar clic
    link = models.CharField(max_length=255, blank=True, null=True) 

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif para {self.recipient}: {self.message}"
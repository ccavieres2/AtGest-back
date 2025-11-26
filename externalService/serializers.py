# externalService/serializers.py
from rest_framework import serializers
from .models import ExternalService
import json # 👈 1. Necesario para arreglar el problema del String

class ExternalServiceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    
    booked_slots = serializers.SerializerMethodField() 

    class Meta:
        model = ExternalService
        fields = [
            'id', 'owner', 'title', 'description', 'category', 'price',
            'duration_minutes', 'available_hours', 'available',
            'created_at', 'image', 'booked_slots'
        ]

    def get_booked_slots(self, obj):
        """
        Busca reservas asociadas. Incluye un try/except por seguridad
        si el modelo de Booking aún no existe o no está importado.
        """
        try:
            # Intentamos importar aquí para evitar errores circulares o si no existe
            from .models import ExternalServiceBooking 
            bookings = ExternalServiceBooking.objects.filter(service=obj)
            
            return [
                {
                    "title": "Reservado",
                    "start": b.start_time.isoformat(),
                    "end": b.end_time.isoformat()
                }
                for b in bookings
            ]
        except (ImportError, NameError):
            return [] # Si no hay sistema de reservas aun, devolvemos lista vacía

    # 👇 2. ESTA ES LA SOLUCIÓN AL ERROR DE PUBLICACIÓN
    def to_internal_value(self, data):
        """
        Intercepta los datos antes de validar.
        Si 'available_hours' llega como texto (porque viene de un FormData con imagen),
        lo convertimos a JSON real (Lista) para que Django no de error.
        """
        # Hacemos una copia mutable de los datos si es necesario
        if hasattr(data, 'dict'):
            data = data.dict()
        elif hasattr(data, 'copy'):
            data = data.copy()

        # Conversión mágica de String -> JSON
        if 'available_hours' in data and isinstance(data['available_hours'], str):
            try:
                data['available_hours'] = json.loads(data['available_hours'])
            except ValueError:
                pass # Si falla, dejamos que la validación normal se encargue
        
        return super().to_internal_value(data)
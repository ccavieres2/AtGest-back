# ccavieres2/atgest-back/AtGest-back-824796a5f5f0a1747c754d4ec544338810379597/externalService/serializers.py

from rest_framework import serializers
from .models import ExternalService
from orders.models import ExternalServiceBooking # 👈 1. Importar el modelo de reservas

class ExternalServiceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    
    # 👈 2. Añadir este nuevo campo
    booked_slots = serializers.SerializerMethodField() 

    class Meta:
        model = ExternalService
        # 👈 3. Modificar "fields" para incluir el nuevo campo
        # (Es mejor ser explícito que usar "__all__" cuando añadimos campos custom)
        fields = [
            'id', 'owner', 'title', 'description', 'category', 'price',
            'duration_minutes', 'available_hours', 'available',
            'created_at', 'image', 'booked_slots' # 👈 Añadido aquí
        ]
        # Nota: Si preferías usar "__all__", puedes dejarlo, pero asegúrate
        # de que el campo 'booked_slots' se esté enviando.

    # 👈 4. Añadir el método que obtiene los datos para "booked_slots"
    def get_booked_slots(self, obj):
        """
        'obj' es la instancia de ExternalService.
        Buscamos todas las reservas (bookings) asociadas a este servicio.
        """
        bookings = ExternalServiceBooking.objects.filter(service=obj)
        
        # Devolvemos una lista simple de eventos para el calendario
        return [
            {
                "title": "Reservado", # Título que se mostrará en el calendario
                "start": b.start_time.isoformat(),
                "end": b.end_time.isoformat()
            }
            for b in bookings
        ]
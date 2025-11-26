from rest_framework import serializers
from .models import ExternalService

class ExternalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalService
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')
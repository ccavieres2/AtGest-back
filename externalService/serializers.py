# externalService/serializers.py
from rest_framework import serializers
from .models import ExternalService

class ExternalServiceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = ExternalService
        fields = "__all__"

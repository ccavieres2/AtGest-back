# orders/serializers.py
from rest_framework import serializers
from .models import WorkOrder
from evaluations.serializers import EvaluationSerializer

class WorkOrderSerializer(serializers.ModelSerializer):
    evaluation_data = EvaluationSerializer(source='evaluation', read_only=True)
    mechanic_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    updated_by_role = serializers.SerializerMethodField()

    class Meta:
        model = WorkOrder
        fields = [
            'id', 
            'folio',  # 👈 DEBE ESTAR AQUÍ
            'evaluation', 'evaluation_data', 
            'owner', 
            'mechanic', 'mechanic_name', 
            'status', 
            'last_status_change_by',
            'updated_by_name',
            'updated_by_role',
            'start_date', 'end_date', 'internal_notes', 
            'created_at'
        ]
        read_only_fields = ['owner', 'created_at']

    def get_mechanic_name(self, obj):
        if obj.mechanic: return obj.mechanic.username
        return None

    def get_updated_by_name(self, obj):
        if obj.last_status_change_by: return obj.last_status_change_by.username
        return None

    def get_updated_by_role(self, obj):
        try:
            if obj.last_status_change_by and hasattr(obj.last_status_change_by, 'profile'):
                return obj.last_status_change_by.profile.get_role_display()
        except: pass
        return None
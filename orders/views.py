from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import WorkOrder
from .serializers import WorkOrderSerializer
from accounts.utils import get_data_owner

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        target_user = get_data_owner(self.request.user)
        return WorkOrder.objects.filter(owner=target_user).order_by('-created_at')

    def perform_create(self, serializer):
        target_user = get_data_owner(self.request.user)
        serializer.save(owner=target_user)
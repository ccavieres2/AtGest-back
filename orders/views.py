# orders/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework.decorators import action
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db import transaction # Importante para atomicidad

from .models import WorkOrder
from .serializers import WorkOrderSerializer
from evaluations.models import Evaluation
# 👇 CAMBIO: Importamos InventoryBatch (donde está el stock real)
from inventory.models import InventoryBatch 
from clients.models import Client, Vehicle 
from external.models import ServiceRequest
from accounts.models import Notification
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

    def perform_update(self, serializer):
        if 'status' in self.request.data:
            serializer.save(last_status_change_by=self.request.user)
        else:
            serializer.save()

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        target_user = get_data_owner(request.user)
        
        # KPIs
        active_orders = WorkOrder.objects.filter(owner=target_user, status__in=['pending', 'in_progress', 'waiting_parts']).count()
        finished_orders = WorkOrder.objects.filter(owner=target_user, status__in=['finished', 'delivered']).count()
        draft_evals = Evaluation.objects.filter(owner=target_user, status='draft').count()
        approved_evals = Evaluation.objects.filter(owner=target_user, status='approved').count()
        rejected_evals = Evaluation.objects.filter(owner=target_user, status='rejected').count()
        total_clients = Client.objects.filter(owner=target_user).count()
        total_vehicles = Vehicle.objects.filter(client__owner=target_user).count()

        # Stock bajo: Buscamos productos cuyo stock total (suma de lotes) sea bajo
        # Esta query es compleja, por simplicidad contaremos lotes con poco stock
        low_stock = InventoryBatch.objects.filter(
            product__owner=target_user, 
            current_quantity__lte=5,
            current_quantity__gt=0
        ).count()

        # Gráficos
        orders_by_status = WorkOrder.objects.filter(owner=target_user).values('status').annotate(count=Count('id'))
        
        today = timezone.now()
        six_months_ago = today - timedelta(days=180)
        
        revenue_orders_qs = WorkOrder.objects.filter(
            owner=target_user,
            status__in=['finished', 'delivered'],
            updated_at__gte=six_months_ago
        ).prefetch_related('evaluation__items')

        revenue_per_month = {}
        for i in range(5, -1, -1):
            d = today - timedelta(days=i*30)
            key = d.strftime("%Y-%m")
            revenue_per_month[key] = 0
            
        for order in revenue_orders_qs:
            total = sum(item.price for item in order.evaluation.items.all() if item.is_approved)
            month_key = order.updated_at.strftime("%Y-%m")
            if month_key in revenue_per_month:
                revenue_per_month[month_key] += total
                
        revenue_chart_data = [{"name": k, "total": v} for k, v in revenue_per_month.items()]

        return Response({
            "kpis": {
                "active_orders": active_orders,
                "finished_orders": finished_orders,
                "pending_evals": 0, # Placeholder
                "draft_evals": draft_evals,
                "approved_evals": approved_evals,
                "rejected_evals": rejected_evals,
                "low_stock": low_stock,
                "total_clients": total_clients,
                "total_vehicles": total_vehicles
            },
            "pie_data": list(orders_by_status),
            "bar_data": revenue_chart_data
        })
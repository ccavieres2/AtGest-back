# orders/views.py
from rest_framework import viewsets, permissions
from rest_framework.views import APIView 
from rest_framework.response import Response 
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import WorkOrder
from .serializers import WorkOrderSerializer
from evaluations.models import Evaluation
from inventory.models import InventoryItem
# 👇 IMPORTAMOS EL MODELO VEHICLE
from clients.models import Client, Vehicle 
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

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        target_user = get_data_owner(request.user)
        
        # --- 1. KPIs Generales ---
        
        active_orders = WorkOrder.objects.filter(
            owner=target_user, 
            status__in=['pending', 'in_progress', 'waiting_parts']
        ).count()
        
        finished_orders = WorkOrder.objects.filter(
            owner=target_user, 
            status__in=['finished', 'delivered']
        ).count()
        
        pending_evals = Evaluation.objects.filter(
            owner=target_user, 
            status__in=['draft', 'sent']
        ).count()

        draft_evals = Evaluation.objects.filter(
            owner=target_user, status='draft'
        ).count()
        
        approved_evals = Evaluation.objects.filter(
            owner=target_user, status='approved'
        ).count()

        rejected_evals = Evaluation.objects.filter(
            owner=target_user, status='rejected'
        ).count()
        
        low_stock = InventoryItem.objects.filter(
            owner=target_user, 
            quantity__lte=5,
            status='active'
        ).count()
        
        total_clients = Client.objects.filter(
            owner=target_user
        ).count()

        # 👇 NUEVO: Total de Vehículos
        # Filtramos vehículos cuyo dueño del cliente sea el usuario actual
        total_vehicles = Vehicle.objects.filter(
            client__owner=target_user
        ).count()

        # --- 2. Gráficos ---
        
        orders_by_status = WorkOrder.objects.filter(owner=target_user).values('status').annotate(count=Count('id'))
        
        today = timezone.now()
        six_months_ago = today - timedelta(days=180)
        
        revenue_orders_qs = WorkOrder.objects.filter(
            owner=target_user,
            status__in=['finished', 'delivered'],
            updated_at__gte=six_months_ago
        ).select_related('evaluation').prefetch_related('evaluation__items')

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
                "pending_evals": pending_evals,
                "draft_evals": draft_evals,
                "approved_evals": approved_evals,
                "rejected_evals": rejected_evals,
                "low_stock": low_stock,
                "total_clients": total_clients,
                "total_vehicles": total_vehicles # 👈 Dato nuevo enviado
            },
            "pie_data": list(orders_by_status),
            "bar_data": revenue_chart_data
        })
        

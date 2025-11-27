from django.urls import path # 👈 Importar path
from rest_framework.routers import DefaultRouter
from .views import WorkOrderViewSet, DashboardStatsView # 👈 Importar la nueva vista

router = DefaultRouter()
router.register(r'orders', WorkOrderViewSet, basename='orders')

urlpatterns = [
    # Ruta personalizada para las estadísticas
    path('orders/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
] + router.urls
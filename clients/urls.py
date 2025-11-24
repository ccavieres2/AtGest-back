# clients/urls.py
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, VehicleViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'vehicles', VehicleViewSet, basename='vehicles') # 👈 NUEVO

urlpatterns = router.urls
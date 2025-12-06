# inventory/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, InventoryBatchViewSet

router = DefaultRouter()
# Rutas para el catálogo
router.register(r"products", ProductViewSet, basename="products")
# Rutas para registrar entradas/lotes
router.register(r"batches", InventoryBatchViewSet, basename="batches")

urlpatterns = router.urls
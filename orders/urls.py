from rest_framework.routers import DefaultRouter
from .views import WorkOrderViewSet

router = DefaultRouter()
router.register(r'orders', WorkOrderViewSet, basename='orders')

urlpatterns = router.urls
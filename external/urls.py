from rest_framework.routers import DefaultRouter
from .views import ExternalServiceViewSet

router = DefaultRouter()
router.register(r'external', ExternalServiceViewSet, basename='external')

urlpatterns = router.urls
# external/urls.py
from rest_framework.routers import DefaultRouter
from .views import ExternalServiceViewSet, ServiceRequestViewSet, MessageViewSet # 👈 Agrega ServiceRequestViewSet

router = DefaultRouter()
router.register(r'external', ExternalServiceViewSet, basename='external')
router.register(r'requests', ServiceRequestViewSet, basename='requests') # 👈 AGREGA ESTA LÍNEA
router.register(r'messages', MessageViewSet, basename='messages')

urlpatterns = router.urls
# externalService/urls.py
from rest_framework.routers import DefaultRouter
from .views import ExternalServiceViewSet

router = DefaultRouter()
router.register(r'external-services', ExternalServiceViewSet, basename='externalservice')

urlpatterns = router.urls

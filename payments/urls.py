from django.urls import path
from . import views

urlpatterns = [
    path('api/orders/<str:order_id>/capture/', views.capture_paypal_order, name='capture-paypal-order'),
]
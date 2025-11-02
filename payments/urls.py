# atgest-back/payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ❗️ CORRECCIÓN: Quitamos 'api/' de aquí
    path('register-and-pay/', views.register_and_pay, name='register-and-pay'),
    
    # ❗️ CORRECCIÓN: Quitamos 'api/' de aquí
    path('orders/<str:order_id>/capture/', views.capture_paypal_order, name='capture-paypal-order'),
]
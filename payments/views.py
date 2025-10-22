import requests
from django.http import JsonResponse
from django.conf import settings
import json

# Función para obtener un token de acceso de PayPal
def get_paypal_access_token():
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(f"{settings.PAYPAL_API_BASE}/v1/oauth2/token", auth=auth, headers=headers, data=data)
    
    if response.status_code != 200:
        # Manejar error
        return None
        
    return response.json()['access_token']

# Vista para capturar el pago
def capture_paypal_order(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    access_token = get_paypal_access_token()
    if not access_token:
        return JsonResponse({"error": "No se pudo autenticar con PayPal"}, status=500)

    capture_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.post(capture_url, headers=headers)
    response_data = response.json()

    if response.status_code == 201 or response.status_code == 200:
        # IMPORTANTE: Aquí verificas el estado y el monto del pago
        # Compara response_data['purchase_units'][0]['amount']['value'] con el precio real de tu producto
        # para evitar que el usuario manipule el precio en el frontend.
        status = response_data.get('status')
        if status == 'COMPLETED':
            # ¡Éxito! El pago fue capturado.
            # Aquí actualizas tu base de datos: marca la orden como pagada,
            # registra el ID de la transacción de PayPal (response_data['id']), etc.
            
            # Ejemplo:
            # mi_orden = Order.objects.get(...)
            # mi_orden.is_paid = True
            # mi_orden.paypal_transaction_id = response_data['id']
            # mi_orden.save()

            return JsonResponse(response_data, status=200)
    
    # Si el pago no fue completado o hubo un error
    return JsonResponse(response_data, status=response.status_code)
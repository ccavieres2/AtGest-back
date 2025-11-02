# atgest-back/payments/views.py
import requests
import json
from decimal import Decimal
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.models import User

# Importa el serializador de registro y el nuevo modelo de pago
from accounts.serializers import RegisterSerializer
from .models import UserPayment


# --- 1. FUNCIÓN HELPER: OBTENER TOKEN ---
# (Sin cambios, solo la movemos arriba)
def get_paypal_access_token():
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    
    response = requests.post(f"{settings.PAYPAL_API_BASE}/v1/oauth2/token", auth=auth, headers=headers, data=data)
    
    if response.status_code != 200:
        print(f"Error al obtener token de PayPal: {response.text}")
        return None
        
    return response.json()['access_token']


# --- 2. FUNCIÓN HELPER: CAPTURAR PAGO ---
# (Nueva función reutilizable que hace la captura)
def capture_paypal_payment(order_id, access_token):
    capture_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post(capture_url, headers=headers)
    return response.json(), response.status_code


# --- 3. VISTA NUEVA: REGISTRAR Y PAGAR ---
@csrf_exempt # Necesario porque es un POST sin autenticación de sesión
@transaction.atomic # Si algo falla (crear usuario o guardar pago), se revierte todo
def register_and_pay(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        paypal_order_id = data.get('paypal_order_id')
        user_data = data.get('user_data')
        
        if not paypal_order_id or not user_data:
            return JsonResponse({"error": "Faltan datos de pago o de usuario"}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    # --- PASO A: Capturar el pago ---
    access_token = get_paypal_access_token()
    if not access_token:
        return JsonResponse({"error": "No se pudo autenticar con PayPal"}, status=500)
    
    response_data, status_code = capture_paypal_payment(paypal_order_id, access_token)

    # Si el pago no fue completado, rechazar
    if status_code not in (200, 201) or response_data.get('status') != 'COMPLETED':
        return JsonResponse({
            "error": "El pago no pudo ser completado. No se creó el usuario.", 
            "details": response_data
        }, status=402) # 402 = Payment Required

    # --- PASO B: El pago fue exitoso, crear el usuario ---
    serializer = RegisterSerializer(data=user_data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            
            # --- PASO C: Guardar el recibo del pago ---
            try:
                purchase_unit = response_data['purchase_units'][0]
                amount_data = purchase_unit['payments']['captures'][0]['amount']
                
                UserPayment.objects.create(
                    user=user,
                    paypal_order_id=response_data['id'],
                    amount=Decimal(amount_data['value']),
                    currency=amount_data['currency_code'],
                    status=response_data['status']
                )
            except (KeyError, Decimal.InvalidOperation) as e:
                # El usuario se creó, pero el recibo falló.
                # @transaction.atomic revertirá la creación del usuario.
                return JsonResponse({
                    "error": f"Pago exitoso, pero error al guardar recibo: {str(e)}. No se creó el usuario.", 
                    "details": response_data
                }, status=500)

            # --- PASO D: Todo exitoso ---
            return JsonResponse({"message": "¡Usuario registrado y pago completado!", "username": user.username}, status=201)
        
        except Exception as e:
            # Error al crear el usuario (ej: username ya existe)
            # @transaction.atomic lo revierte.
             return JsonResponse({
                "error": "El pago fue exitoso, pero el registro falló. (¿Usuario o email ya existen?)", 
                "details": str(e)
            }, status=400)

    else:
        # Los datos del usuario no eran válidos (ej: passwords no coinciden)
        # @transaction.atomic lo revierte.
        return JsonResponse({
            "error": "El pago fue exitoso, pero los datos de registro son inválidos.", 
            "details": serializer.errors
        }, status=400)


# --- 4. VISTA ANTIGUA: CAPTURAR ORDEN (Para otros pagos futuros) ---
# (La dejamos como estaba, pero ahora usa el helper)
def capture_paypal_order(request, order_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    access_token = get_paypal_access_token()
    if not access_token:
        return JsonResponse({"error": "No se pudo autenticar con PayPal"}, status=500)

    response_data, status_code = capture_paypal_payment(order_id, access_token)

    if (status_code == 201 or status_code == 200) and response_data.get('status') == 'COMPLETED':
        # IMPORTANTE: Aquí deberías vincular este pago a una *orden existente*
        # (No a un usuario nuevo)
        
        # P.ej: mi_orden = Order.objects.get(id=...)
        # mi_orden.status = "pagado"
        # mi_orden.save()
        
        # O guardar un UserPayment
        # user = request.user 
        # UserPayment.objects.create(...)

        return JsonResponse(response_data, status=200)
    
    return JsonResponse(response_data, status=status_code)
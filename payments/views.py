# atgest-back/payments/views.py
import requests
import json
from decimal import Decimal
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
import threading  # 👈 --- 1. IMPORTA threading ---

from accounts.serializers import RegisterSerializer
from .models import UserPayment

# ... (Las funciones get_paypal_access_token y capture_paypal_payment no cambian) ...
def get_paypal_access_token():
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(f"{settings.PAYPAL_API_BASE}/v1/oauth2/token", auth=auth, headers=headers, data=data)
    if response.status_code != 200:
        print(f"Error al obtener token de PayPal: {response.text}")
        return None
    return response.json()['access_token']

def capture_paypal_payment(order_id, access_token):
    capture_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post(capture_url, headers=headers)
    return response.json(), response.status_code


# 👈 --- 2. CREA UNA FUNCIÓN PARA ENVIAR EL CORREO ---
def send_welcome_email_async(user, payment_obj):
    """
    Función que se ejecutará en un hilo separado para no bloquear la respuesta.
    """
    try:
        subject = "¡Bienvenido a AtGest! Confirmación de registro y pago"
        
        message_body = f"""
        ¡Hola, {user.username}!

        Gracias por registrarte y completar tu suscripción en AtGest.
        
        Aquí están los detalles de tu pago:
        - ID de Transacción PayPal: {payment_obj.paypal_order_id}
        - Monto: {payment_obj.amount} {payment_obj.currency}
        - Estado: {payment_obj.status}
        - Fecha: {payment_obj.created_at.strftime('%Y-%m-%d %H:%M')}

        ¡Ya puedes iniciar sesión en la plataforma!

        Saludos,
        El equipo de AtGest
        """
        
        send_mail(
            subject,
            message_body,
            settings.EMAIL_HOST_USER,  # Remitente
            [user.email],              # Destinatario
            fail_silently=False,
        )
        print(f"Email de bienvenida enviado exitosamente a {user.email}")
        
    except Exception as email_error:
        # Como esto corre en segundo plano, el print es nuestra única forma
        # de saber si falló (o usar logging).
        print(f"ERROR ASÍNCRONO al enviar email de bienvenida a {user.email}: {str(email_error)}")


# --- 3. VISTA: REGISTRAR Y PAGAR (Modificada) ---
@csrf_exempt
@transaction.atomic
def register_and_pay(request):
    # ... (El inicio de la función no cambia) ...
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
    # ... (Sin cambios) ...
    access_token = get_paypal_access_token()
    if not access_token:
        return JsonResponse({"error": "No se pudo autenticar con PayPal"}, status=500)
    response_data, status_code = capture_paypal_payment(paypal_order_id, access_token)
    if status_code not in (200, 201) or response_data.get('status') != 'COMPLETED':
        return JsonResponse({
            "error": "El pago no pudo ser completado. No se creó el usuario.", 
            "details": response_data
        }, status=402)

    # --- PASO B: El pago fue exitoso, crear el usuario ---
    serializer = RegisterSerializer(data=user_data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            
            # --- PASO C: Guardar el recibo del pago ---
            payment_obj = None
            try:
                purchase_unit = response_data['purchase_units'][0]
                amount_data = purchase_unit['payments']['captures'][0]['amount']
                payment_obj = UserPayment.objects.create(
                    user=user,
                    paypal_order_id=response_data['id'],
                    amount=Decimal(amount_data['value']),
                    currency=amount_data['currency_code'],
                    status=response_data['status']
                )
            except (KeyError, Decimal.InvalidOperation) as e:
                return JsonResponse({
                    "error": f"Pago exitoso, pero error al guardar recibo: {str(e)}. No se creó el usuario.", 
                    "details": response_data
                }, status=500)

            # --- ⭐️ PASO D: Enviar email (AHORA ASÍNCRONO) ⭐️ ---
            if user and payment_obj:
                # 👈 --- 3. INICIA LA FUNCIÓN EN UN HILO SEPARADO ---
                email_thread = threading.Thread(
                    target=send_welcome_email_async, 
                    args=(user, payment_obj)
                )
                email_thread.start() # 👈 Esto se ejecuta instantáneamente

            # --- PASO E: Todo exitoso (Respuesta al frontend) ---
            # 👈 Esta respuesta ahora es INMEDIATA. No espera el correo.
            return JsonResponse({"message": "¡Usuario registrado y pago completado!", "username": user.username}, status=201)
        
        # ... (El resto de los 'except' y 'else' no cambian) ...
        except Exception as e:
             return JsonResponse({
                "error": "El pago fue exitoso, pero el registro falló. (¿Usuario o email ya existen?)", 
                "details": str(e)
            }, status=400)
    else:
        return JsonResponse({
            "error": "El pago fue exitoso, pero los datos de registro son inválidos.", 
            "details": serializer.errors
        }, status=400)


# --- 4. VISTA ANTIGUA: CAPTURAR ORDEN (Sin cambios) ---
def capture_paypal_order(request, order_id):
    # ... (Sin cambios) ...
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    access_token = get_paypal_access_token()
    if not access_token:
        return JsonResponse({"error": "No se pudo autenticar con PayPal"}, status=500)
    response_data, status_code = capture_paypal_payment(order_id, access_token)
    if (status_code == 201 or status_code == 200) and response_data.get('status') == 'COMPLETED':
        return JsonResponse(response_data, status=200)
    return JsonResponse(response_data, status=status_code)
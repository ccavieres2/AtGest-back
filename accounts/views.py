# accounts/views.py
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from .models import UserProfile
from django.shortcuts import get_object_or_404
from .utils import get_data_owner  # 👈 IMPORTANTE: Importar la utilidad corregida
from django.db import IntegrityError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
User = get_user_model()

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Usuario registrado con éxito.", "username": user.username}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        identifier = request.data.get("identifier")
        password   = request.data.get("password")
        if not identifier or not password:
            return Response({"detail": "Falta usuario/email o contraseña."}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(Q(email__iexact=identifier))
            except User.DoesNotExist:
                return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        user_auth = authenticate(username=user.username, password=password)
        if not user_auth:
            return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user_auth)
        
        role = 'owner'
        if hasattr(user_auth, 'profile'):
            role = user_auth.profile.role

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user_auth.username,
            "email": user_auth.email,
            "role": role,
        }, status=status.HTTP_200_OK)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        u = request.user
        role = 'owner'
        if hasattr(u, 'profile'):
            role = u.profile.role
            
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": role,
            # Agregamos phone si existe en el perfil
            "phone": u.profile.phone if hasattr(u, 'profile') else "" 
        })

    # 👇 AGREGAR ESTE MÉTODO PUT 👇
    def put(self, request):
        user = request.user
        data = request.data

        # 1. Validar Username único (si cambió)
        new_username = data.get("username")
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exists():
                return Response({"error": "El nombre de usuario ya está en uso."}, status=400)
            user.username = new_username

        # 2. Validar Email único (si cambió)
        new_email = data.get("email")
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exists():
                return Response({"error": "El correo electrónico ya está en uso."}, status=400)
            user.email = new_email

        # 3. Actualizar Contraseña (si se envía)
        new_password = data.get("password")
        if new_password and new_password.strip():
            if len(new_password) < 8:
                return Response({"error": "La contraseña debe tener al menos 8 caracteres."}, status=400)
            user.set_password(new_password)

        # 4. Actualizar Teléfono (en el perfil)
        new_phone = data.get("phone")
        if new_phone is not None and hasattr(user, 'profile'):
            user.profile.phone = new_phone
            user.profile.save()

        try:
            user.save()
            return Response({"message": "Perfil actualizado correctamente."}, status=200)
        except Exception as e:
            return Response({"error": f"Error al guardar: {str(e)}"}, status=400)

class CreateMechanicView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # --- CORRECCIÓN IMPLEMENTADA AQUÍ ---
        # Usamos get_data_owner para obtener al "jefe" real.
        # Si el usuario es mecánico, target_user será su jefe.
        # Si el usuario es dueño, target_user será él mismo.
        target_user = get_data_owner(request.user)
        
        # Filtramos los perfiles que trabajan para ese jefe
        profiles = UserProfile.objects.filter(employer=target_user).select_related('user')
        
        data = []
        for p in profiles:
            data.append({
                "id": p.user.id,
                "username": p.user.username,
                "email": p.user.email,
                "phone": p.phone,
                "date_joined": p.user.date_joined,
                "role": p.get_role_display()
            })

        return Response(data, status=200)

    def post(self, request):
        # Para CREAR (POST), mantenemos la restricción estricta: SOLO DUEÑOS
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'owner':
             return Response({"error": "Solo los dueños pueden registrar personal."}, status=403)

        data = request.data
        username = data.get("username")
        email = data.get("email")
        role = data.get("role")
        password = data.get("password")
        phone = data.get("phone", "")

        if not username or not password or not email or not role or not phone:
             return Response({"error": "Faltan datos obligatorios"}, status=400)
             
        allowed_roles = ['mechanic', 'assistant', 'admin']
        if role not in allowed_roles:
             return Response({"error": "Rol no válido."}, status=400)

        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            return Response({"error": "Usuario o email ya registrados."}, status=400)

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': role,
                    'phone': phone,
                    'employer': request.user
                }
            )

            return Response({"message": "Creado con éxito", "username": user.username}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class MechanicDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_employee(self, request, pk):
        # Solo el dueño puede editar/borrar a sus empleados
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'owner': return None
        employee = get_object_or_404(User, pk=pk)
        if not hasattr(employee, 'profile') or employee.profile.employer != request.user: return None
        return employee

    def put(self, request, pk):
        employee = self.get_employee(request, pk)
        if not employee:
            return Response({"error": "No tienes permiso."}, status=403)

        data = request.data
        
        if 'username' in data: employee.username = data['username']
        if 'email' in data: employee.email = data['email']
        if 'password' in data and data['password'].strip():
            employee.set_password(data['password'])
        
        try:
            employee.save()
            
            profile_updated = False
            if 'role' in data:
                employee.profile.role = data['role']
                profile_updated = True
            
            if 'phone' in data:
                employee.profile.phone = data['phone']
                profile_updated = True
            
            if profile_updated:
                employee.profile.save()

            return Response({"message": "Actualizado correctamente."}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def delete(self, request, pk):
        employee = self.get_employee(request, pk)
        if not employee: return Response({"error": "Error."}, status=403)
        employee.delete()
        return Response({"message": "Eliminado."}, status=200)
    
class RequestPasswordResetView(APIView):
    permission_classes = [] # Público

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "El email es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Por seguridad, no decimos si el usuario no existe, pero retornamos éxito simulado
            # O puedes retornar error si prefieres ser explícito.
            return Response({"message": "Si el correo existe, se ha enviado un enlace."}, status=200)

        # 👇 REGLA DE NEGOCIO: VALIDAR SI ES OWNER 👇
        if hasattr(user, 'profile') and user.profile.role != 'owner':
            return Response(
                {"error": "Tu cuenta no tiene permisos para restablecer contraseña aquí. Contacta al dueño del taller."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Generar token y uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Construir enlace (Asegúrate de que coincida con la ruta del frontend)
        # Asumimos que el front corre en localhost:5173 según tu configuración
        reset_link = f"http://localhost:5173/reset-password/{uid}/{token}"

        # Enviar correo
        try:
            send_mail(
                subject="Recuperación de Contraseña - AtGest",
                message=f"Hola {user.username},\n\nPara restablecer tu contraseña, haz clic en el siguiente enlace:\n\n{reset_link}\n\nSi no solicitaste esto, ignora este mensaje.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({"error": "Error al enviar el correo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Si el correo existe y es válido, se ha enviado un enlace."}, status=200)


class ResetPasswordConfirmView(APIView):
    permission_classes = [] # Público

    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')

        if not uidb64 or not token or not password:
            return Response({"error": "Faltan datos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Enlace inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace ha expirado o es inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # Cambiar contraseña
        user.set_password(password)
        user.save()

        return Response({"message": "Contraseña restablecida con éxito. Ya puedes iniciar sesión."}, status=200)
    
    
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Obtener notificaciones del usuario actual (no leídas primero)
        notifs = Notification.objects.filter(recipient=request.user).order_by('is_read', '-created_at')[:20]
        serializer = NotificationSerializer(notifs, many=True)
        return Response(serializer.data)

    def put(self, request):
        # Marcar todas como leídas
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"status": "marked as read"})
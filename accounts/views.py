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
        })

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
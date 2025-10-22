# accounts/views.py
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer  # ya lo tienes

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
    """Permite login con username o email + password, devuelve JWT (access, refresh)."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        identifier = request.data.get("identifier")  # username o email
        password   = request.data.get("password")
        if not identifier or not password:
            return Response({"detail": "Falta usuario/email o contraseña."}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        # 1) intentar por username
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            # 2) intentar por email
            try:
                user = User.objects.get(Q(email__iexact=identifier))
            except User.DoesNotExist:
                return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        # usar authenticate necesita username
        user_auth = authenticate(username=user.username, password=password)
        if not user_auth:
            return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user_auth)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user_auth.username,
            "email": user_auth.email,
        }, status=status.HTTP_200_OK)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
        })

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir que solo los propietarios de un objeto
    puedan editarlo, pero permitir que cualquiera pueda leerlo.
    """
    def has_object_permission(self, request, view, obj):
        # Los permisos de LECTURA (GET, HEAD, OPTIONS) se permiten a cualquier solicitud.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Los permisos de ESCRITURA (PUT, PATCH, DELETE) solo se permiten
        # al propietario (owner) del servicio.
        return obj.owner == request.user
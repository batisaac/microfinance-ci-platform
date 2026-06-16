from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "agent"


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "client"


class IsAdminOrAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("admin", "agent")


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.role == "admin"
